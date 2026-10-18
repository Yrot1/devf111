from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decrypt_token
from app.db.models import Issue, PRFile, PRReviewComment, PullRequest, Repository, WorkflowRun
from app.schemas.repos import RepoSyncRequest, RepoSyncResponse
from app.services.github.actions import get_workflow_run_logs, list_workflow_run_jobs, list_workflow_runs
from app.services.github.issues import list_issues
from app.services.github.pull_requests import list_pull_request_files, list_pull_request_review_comments, list_pull_requests


def parse_github_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def login_of(user: dict | None) -> str | None:
    return user.get("login") if user else None


async def sync_repository(db: Session, repo: Repository, payload: RepoSyncRequest) -> RepoSyncResponse:
    """把某个 GitHub 仓库的 Issue / PR / CI 数据同步进本地数据库。

    整体流程（按顺序执行）：
        1. 校验仓库类型，准备 token、计数器，以及每个数据源的状态「记账本」；
        2. 按 payload 的勾选项，依次同步 Issue、PR（含改动文件与 Review 评论）、
           Workflow Run（含 Job 与失败日志）；
        3. 汇总三个数据源的状态，得出本次同步的总体结论；
        4. 把结论写回 repo.sync_metadata，提交事务并返回。

    函数是幂等的：重复调用只会更新已有记录，不会产生重复行。

    Args:
        db: 数据库会话。由调用方创建，本函数在最后负责 commit。
        repo: 目标仓库，提供 owner / name / api_base_url 与加密后的 token。
        payload: 本次同步哪些数据源，以及每个数据源的条数上限（limit=None 表示全部分页）。

    Returns:
        RepoSyncResponse：总体状态、各数据源明细、处理条数与失败原因。
    """
    # 目前只实现了 GitHub 官方 API 和 GitHub 兼容 API，其它 provider（如 GitLab）直接拒绝。
    if repo.provider not in {"github", "github_compatible"}:
        raise HTTPException(status_code=400, detail=f"{repo.provider} sync is not implemented yet")

    # synced：记录本次「处理了多少条」，同时也定义了三个数据源的名字（下面靠它循环初始化）。
    synced = {"issues": 0, "pull_requests": 0, "workflow_runs": 0}
    # 库里存的是加密 token，用之前先解密；没配 token 就用匿名请求（会受更严格的限流）。
    token = decrypt_token(repo.github_token_encrypted, settings.token_encryption_key) if repo.github_token_encrypted else None
    # 每个仓库可以自带 API 地址，用于 GitHub Enterprise 或反向代理。
    base_url = repo.api_base_url
    # sources：每个数据源的状态记账本。初始为 skipped，代表「这次没勾选」。
    #   status:   skipped / empty / completed / partial / failed
    #   count:    实际拿到的条数
    #   complete: 是否把该源的分页全部拉完（撞到 limit 上限时为 False）
    #   pages:    实际请求了几页（GitHub 每页最多 100 条）
    sources = {key: {"status": "skipped", "count": 0, "complete": False, "pages": 0} for key in synced}
    # 收集失败原因，最终原样返回给前端，方便定位到底是哪个接口挂了。
    errors: list[str] = []

    async def fetch(source: str, loader, *args, detail: str | None = None, **kwargs):
        """调用一个 GitHub 接口，并统一完成「记账 + 容错」。

        `detail` 是理解这个闭包的关键，它区分了两种粒度的请求：
          - detail 为 None：主资源（Issue 列表 / PR 列表 / Run 列表）。
            它失败意味着「这一类数据一条都没拿到」，标记为 failed。
          - detail 不为 None：主记录下面的子资源（某个 PR 的改动文件、Review 评论，
            某个 Run 的 jobs / logs）。它失败时主数据其实已经拿到了，
            所以只标记为 partial，不会把整体结论拉低成 failed。

        出错时统一返回 None，调用方用 `xxx or []` 或 `if xxx is not None` 跳过，
        这样本地已有的旧数据不会被清空。
        """
        try:
            items = await loader(*args, **kwargs)
        except (httpx.HTTPError, ValueError) as exc:
            # httpx.HTTPError 覆盖网络异常与 4xx/5xx；
            # ValueError 来自 GitHubClient 对「响应结构异常 / 分页跳转异常」的主动校验。
            reason = f"HTTP {exc.response.status_code}" if isinstance(exc, httpx.HTTPStatusError) else type(exc).__name__
            # 错误信息带上 detail，能精确定位到是哪个 PR / 哪个 Run 出的问题。
            message = f"{source}{'/' + detail if detail else ''}: {reason}"
            errors.append(message)
            sources[source]["status"] = "partial" if detail else "failed"
            sources[source]["complete"] = False
            return None
        if detail is None:
            # 只有主资源才改写 status / count / pages，子资源不覆盖这些统计。
            complete = getattr(items, "complete", True)
            sources[source] = {
                # 拉全了且有数据 -> completed；拉全了但没数据 -> empty（empty 不等于失败）；
                # 撞到 limit 上限没拉全 -> partial。
                "status": ("completed" if items else "empty") if complete else "partial",
                "count": len(items), "complete": complete, "pages": getattr(items, "pages", 1),
            }
        return items

    # ===================== 1) Issue =====================
    if payload.sync_issues:
        remote_issues = await fetch("issues", list_issues, repo.owner, repo.name, token=token, limit=payload.limit, base_url=base_url)
        # 一整类请求失败时 remote_issues 是 None，`or []` 保证循环安全跳过。
        for item in remote_issues or []:
            # upsert：先按 GitHub 的 issue id 查本地记录，有就更新，没有才新建。
            issue = db.query(Issue).filter(Issue.repo_id == repo.id, Issue.github_issue_id == item.get("id")).one_or_none()
            if issue is None:
                issue = Issue(repo_id=repo.id, github_issue_id=item.get("id"), number=item.get("number", 0), title=item.get("title") or "")
                db.add(issue)
            # 下面把 GitHub 字段逐个映射到本地列。
            # 关键字段（number / title / state）用 `or 旧值` 兜底：远端返回 null 时保留本地值，
            # 避免一次脏响应把已有数据洗成空。
            issue.number = item.get("number", issue.number)
            issue.title = item.get("title") or issue.title
            issue.body = item.get("body")
            issue.state = item.get("state") or "open"
            issue.labels = [label.get("name") for label in item.get("labels", []) if label.get("name")]
            issue.author = login_of(item.get("user"))
            issue.assignees = [login_of(user) for user in item.get("assignees", []) if login_of(user)]
            # GitHub 的时间是带 Z 的 ISO8601 字符串，统一转成带时区的 datetime。
            issue.created_at = parse_github_datetime(item.get("created_at"))
            issue.updated_at = parse_github_datetime(item.get("updated_at"))
            issue.closed_at = parse_github_datetime(item.get("closed_at"))
            synced["issues"] += 1

    # ===================== 2) Pull Request（含改动文件与 Review 评论） =====================
    if payload.sync_pull_requests:
        remote_prs = await fetch("pull_requests", list_pull_requests, repo.owner, repo.name, token=token, limit=payload.limit, base_url=base_url)
        for item in remote_prs or []:
            # 同样按 github_pr_id 做 upsert。
            pr = db.query(PullRequest).filter(PullRequest.repo_id == repo.id, PullRequest.github_pr_id == item.get("id")).one_or_none()
            if pr is None:
                pr = PullRequest(repo_id=repo.id, github_pr_id=item.get("id"), number=item.get("number", 0), title=item.get("title") or "")
                db.add(pr)
                # 必须 flush：项目关掉了 autoflush，不 flush 就拿不到新记录的主键 pr.id，
                # 下面挂 PRFile / PRReviewComment 时就没法填外键。
                db.flush()
            pr.number = item.get("number", pr.number)
            pr.title = item.get("title") or pr.title
            pr.body = item.get("body")
            pr.state = item.get("state") or "open"
            pr.author = login_of(item.get("user"))
            pr.base_branch = (item.get("base") or {}).get("ref")
            pr.head_branch = (item.get("head") or {}).get("ref")
            pr.merged_at = parse_github_datetime(item.get("merged_at"))
            pr.created_at = parse_github_datetime(item.get("created_at"))
            pr.updated_at = parse_github_datetime(item.get("updated_at"))

            # ---- 该 PR 的改动文件 ----
            # 这里 source 仍然传 "pull_requests"：子资源失败会汇总到同一个数据源上。
            files = await fetch("pull_requests", list_pull_request_files, repo.owner, repo.name, pr.number, token=token, base_url=base_url, detail=f"#{pr.number}/files")
            # 只有拉取成功（files is not None）才删旧记录。
            # 拉取失败时保留上一次同步的文件列表，避免「同步失败反而把数据清空」。
            if files is not None:
                db.query(PRFile).filter(PRFile.pr_id == pr.id).delete()
            # 子资源是「整体替换」语义：先清空再全量写入，不做逐条 upsert。
            for file_item in files or []:
                db.add(
                    PRFile(
                        pr_id=pr.id,
                        filename=file_item.get("filename") or "",
                        status=file_item.get("status") or "modified",
                        additions=file_item.get("additions") or 0,
                        deletions=file_item.get("deletions") or 0,
                        patch=file_item.get("patch"),
                    )
                )
            # ---- 该 PR 的 Review 评论（处理方式与上面的改动文件完全一致） ----
            review_comments = await fetch("pull_requests", list_pull_request_review_comments, repo.owner, repo.name, pr.number, token=token, base_url=base_url, detail=f"#{pr.number}/comments")
            if review_comments is not None:
                db.query(PRReviewComment).filter(PRReviewComment.pr_id == pr.id).delete()
            for comment_item in review_comments or []:
                db.add(
                    PRReviewComment(
                        pr_id=pr.id,
                        github_comment_id=comment_item.get("id"),
                        body=comment_item.get("body"),
                        path=comment_item.get("path"),
                        line=comment_item.get("line") or comment_item.get("original_line"),
                        author=login_of(comment_item.get("user")),
                        created_at=parse_github_datetime(comment_item.get("created_at")),
                        updated_at=parse_github_datetime(comment_item.get("updated_at")),
                    )
                )
            # 主记录处理完了才计数。
            synced["pull_requests"] += 1

    # ===================== 3) Workflow Run（含 Job 与失败日志） =====================
    if payload.sync_workflow_runs:
        remote_runs = await fetch("workflow_runs", list_workflow_runs, repo.owner, repo.name, token=token, limit=payload.limit, base_url=base_url)
        for item in remote_runs or []:
            # 按 github_run_id 做 upsert。
            run = db.query(WorkflowRun).filter(WorkflowRun.repo_id == repo.id, WorkflowRun.github_run_id == item.get("id")).one_or_none()
            if run is None:
                run = WorkflowRun(repo_id=repo.id, github_run_id=item.get("id"), name=item.get("name") or "workflow")
                db.add(run)
            run.name = item.get("name") or run.name
            run.status = item.get("status") or "unknown"
            run.conclusion = item.get("conclusion")
            run.html_url = item.get("html_url")
            run.created_at = parse_github_datetime(item.get("created_at"))
            run.updated_at = parse_github_datetime(item.get("updated_at"))
            if run.github_run_id:
                # 每个 Run 再拉一次 jobs（含 steps）。失败只降级为 partial。
                jobs = await fetch("workflow_runs", list_workflow_run_jobs, repo.owner, repo.name, run.github_run_id, token=token, base_url=base_url, detail=f"{run.github_run_id}/jobs")
                # jobs 是 JSON 列，整体覆盖写回；拉取失败时保留上一次的值。
                if jobs is not None:
                    run.jobs = [
                        {
                            "id": job.get("id"),
                            "name": job.get("name"),
                            "status": job.get("status"),
                            "conclusion": job.get("conclusion"),
                            "html_url": job.get("html_url"),
                            "started_at": job.get("started_at"),
                            "completed_at": job.get("completed_at"),
                            "steps": [
                                {
                                    "name": step.get("name"),
                                    "status": step.get("status"),
                                    "conclusion": step.get("conclusion"),
                                    "number": step.get("number"),
                                }
                                for step in job.get("steps", [])
                            ],
                        }
                        for job in jobs
                    ]
            # 只有失败的 Run 才去拉日志：日志体积大，成功的 Run 拉它没有意义。
            if run.conclusion == "failure" and run.github_run_id:
                logs = await fetch("workflow_runs", get_workflow_run_logs, repo.owner, repo.name, run.github_run_id, token=token, base_url=base_url, detail=f"{run.github_run_id}/logs")
                if logs is not None:
                    run.logs_text = logs
            synced["workflow_runs"] += 1

    # ===================== 汇总本次同步的总体结论 =====================
    # 只看勾选过的源（skipped 代表「没勾」）。
    requested = [item for item in sources.values() if item["status"] != "skipped"]
    if not requested:
        # 三个数据源都没勾。
        status = "skipped"
    elif all(item["status"] == "failed" for item in requested):
        # 勾选的源全军覆没。
        status = "failed"
    elif any(item["status"] in {"failed", "partial"} for item in requested):
        # 有源失败，或有源撞到 limit 上限导致数据不完整。
        status = "partial"
    else:
        # 所有勾选的源都成功：有数据算 completed，没数据算 empty（empty 不能当成失败）。
        status = "completed" if any(synced.values()) else "empty"
    now = datetime.now(timezone.utc)
    messages = {
        "completed": "已完成所选数据源的全部分页同步。",
        "empty": "所选数据源请求成功，但未返回记录；不能据此判断仓库健康。",
        "partial": "同步不完整：存在请求失败或数量上限，请查看各数据源状态。",
        "failed": "同步失败，未获取到有效的新数据；保留已有数据。",
        "skipped": "未选择数据源，没有执行同步。",
    }
    # 只有真正同步成功才刷新 last_sync_at；失败/部分失败保留旧时间，
    # 避免「明明没同步成功，却看起来刚同步过」——仓库健康分析依赖这个字段。
    if status in {"completed", "empty"}:
        repo.last_sync_at = now
    result = RepoSyncResponse(repo_id=repo.id, status=status, synced=synced, sources=sources, errors=errors, message=messages[status])
    # 把完整报告落到仓库行上，供 /sync-status 接口和仓库健康分析读取。
    # attempted_at 记录「这次尝试发生在什么时候」（失败也会更新），与 last_sync_at 语义不同。
    repo.sync_metadata = {**result.model_dump(mode="json"), "attempted_at": now.isoformat(), "limit": payload.limit}
    # 整个过程共用一个事务，到这里才真正写库；中途抛异常会整体回滚。
    db.flush()
    db.commit()
    return result


async def sync_repository_by_id(repo_id: UUID, payload: RepoSyncRequest) -> RepoSyncResponse | None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        repo = db.get(Repository, repo_id)
        if repo is None:
            return None
        return await sync_repository(db, repo, payload)
    finally:
        db.close()
