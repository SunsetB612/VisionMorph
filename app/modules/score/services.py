"""
打分服务
"""
import os
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.modules.score.schemas import ScoreRequest, ScoreResponse, ScoreInfo, GeneratedImageScore

try:
    import pandas as pd
except ImportError:  # pragma: no cover - runtime dependency
    pd = None


_SCORE_COLUMNS = [
    ("overall_score", 1),
    ("score", 1),
    ("评分", 1),
    ("composition_score", 10),
    ("compositionScore", 10),
]

_HIGHLIGHT_COLUMNS = ["highlights", "analysis_suggestions", "style_labels"]
_AI_COMMENT_COLUMNS = ["ai_comment", "analysis_explanation"]
_GUIDANCE_COLUMNS = ["shooting_guidance", "doubao_shooting_suggestions"]


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if pd is not None and pd.isna(value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _normalize_score(raw_value: Any, multiplier: int) -> Optional[int]:
    if _is_empty(raw_value):
        return None

    if isinstance(raw_value, str):
        cleaned = raw_value.strip()
        if not cleaned:
            return None
        cleaned = cleaned.replace("%", "")
        try:
            numeric = float(cleaned)
        except ValueError:
            return None
    else:
        try:
            numeric = float(raw_value)
        except (TypeError, ValueError):
            return None

    score = int(round(numeric * multiplier))
    if score <= 0:
        return None
    return max(1, min(100, score))


def _extract_text(record: Dict[str, Any], candidates: List[str]) -> Optional[str]:
    for field in candidates:
        if field in record and not _is_empty(record[field]):
            return str(record[field]).strip()
    return None


def _resolve_excel_path(user_id: int) -> str:
    excel_dir = os.path.join(settings.UPLOAD_DIR, f"user{user_id}", "excel")
    return os.path.join(excel_dir, f"user{user_id}_crop_report.xlsx")


def _load_excel_scores(user_id: int) -> Dict[int, Dict[str, Optional[str]]]:
    excel_path = _resolve_excel_path(user_id)

    if not os.path.exists(excel_path):
        raise ValueError(f"未找到用户 {user_id} 的评分 Excel 文件：{excel_path}")

    if pd is None:
        raise RuntimeError("未安装 pandas，无法读取 Excel 评分数据")

    try:
        df = pd.read_excel(excel_path)
    except Exception as exc:  # pragma: no cover - I/O 或解析异常
        raise ValueError(f"读取评分 Excel 失败：{exc}") from exc

    if df.empty:
        return {}

    records = df.to_dict(orient="records")
    score_map: Dict[int, Dict[str, Optional[str]]] = {}

    for record in records:
        generated_id = record.get("generated_image_id")
        if _is_empty(generated_id):
            continue

        try:
            generated_id_int = int(generated_id)
        except (TypeError, ValueError):
            continue

        score_value: Optional[int] = None
        for column_name, multiplier in _SCORE_COLUMNS:
            if column_name in record:
                score_value = _normalize_score(record[column_name], multiplier)
                if score_value is not None:
                    break

        if score_value is None:
            continue

        score_map[generated_id_int] = {
            "overall_score": score_value,
            "highlights": _extract_text(record, _HIGHLIGHT_COLUMNS),
            "ai_comment": _extract_text(record, _AI_COMMENT_COLUMNS),
            "shooting_guidance": _extract_text(record, _GUIDANCE_COLUMNS),
        }

    return score_map


def create_scores(db: Session, request: ScoreRequest) -> ScoreResponse:
    """为生成的图片创建或更新评分（基于 Excel 数据）"""

    if pd is None:
        raise RuntimeError("未安装 pandas，无法从 Excel 读取评分数据")

    try:
        generated_images = db.execute(
            text(
                """
                SELECT ti.id, ti.filename, ti.file_path, ti.created_at, i.user_id, u.username
                FROM temp_images ti
                JOIN images i ON ti.original_image_id = i.id
                JOIN users u ON i.user_id = u.id
                WHERE ti.original_image_id = :original_image_id
                ORDER BY ti.created_at DESC
                """
            ),
            {"original_image_id": request.original_image_id},
        ).fetchall()

        if not generated_images:
            raise ValueError("未找到对应的生成图片")

        user_id = generated_images[0][4]
        username = generated_images[0][5]

        excel_scores = _load_excel_scores(user_id)

        if not excel_scores:
            raise ValueError("Excel 报告中未找到任何有效的评分数据")

        scored_count = 0

        for generated_image in generated_images:
            generated_image_id = generated_image[0]

            score_payload = excel_scores.get(generated_image_id)
            if not score_payload:
                continue

            overall_score = score_payload["overall_score"]
            if overall_score is None:
                continue

            existing_score = db.execute(
                text(
                    """
                    SELECT id FROM image_evaluations
                    WHERE generated_image_id = :generated_image_id
                    """
                ),
                {"generated_image_id": generated_image_id},
            ).fetchone()

            if existing_score:
                db.execute(
                    text(
                        """
                        UPDATE image_evaluations
                        SET overall_score = :overall_score,
                            highlights = :highlights,
                            ai_comment = :ai_comment,
                            shooting_guidance = :shooting_guidance
                        WHERE generated_image_id = :generated_image_id
                        """
                    ),
                    {
                        "overall_score": overall_score,
                        "highlights": score_payload["highlights"],
                        "ai_comment": score_payload["ai_comment"],
                        "shooting_guidance": score_payload["shooting_guidance"],
                        "generated_image_id": generated_image_id,
                    },
                )
            else:
                db.execute(
                    text(
                        """
                        INSERT INTO image_evaluations
                        (generated_image_id, overall_score, highlights, ai_comment, shooting_guidance, created_at)
                        VALUES (:generated_image_id, :overall_score, :highlights, :ai_comment, :shooting_guidance, NOW())
                        """
                    ),
                    {
                        "generated_image_id": generated_image_id,
                        "overall_score": overall_score,
                        "highlights": score_payload["highlights"],
                        "ai_comment": score_payload["ai_comment"],
                        "shooting_guidance": score_payload["shooting_guidance"],
                    },
                )

            scored_count += 1

        if scored_count == 0:
            raise ValueError("未在 Excel 中找到与生成图片匹配的评分数据")

        db.commit()

        return ScoreResponse(
            original_image_id=request.original_image_id,
            scored_count=scored_count,
            message=f"成功为用户 {username} 的 {scored_count} 张生成图片同步评分",
        )

    except Exception as e:
        db.rollback()
        print(f"评分失败: {e}")
        raise ValueError(f"评分失败: {str(e)}")


def get_scores_by_original_image(db: Session, original_image_id: int) -> List[GeneratedImageScore]:
    """获取原始图片对应的所有生成图片的评分"""
    results = db.execute(text("""
        SELECT 
            ti.id as generated_image_id,
            ti.filename,
            ti.file_path,
            ie.overall_score,
            ti.created_at
        FROM temp_images ti
        LEFT JOIN image_evaluations ie ON ti.id = ie.generated_image_id
        WHERE ti.original_image_id = :original_image_id
        ORDER BY ti.created_at DESC
    """), {"original_image_id": original_image_id}).fetchall()
    
    return [
        GeneratedImageScore(
            generated_image_id=row[0],
            filename=row[1],
            file_path=row[2],
            overall_score=row[3] if row[3] is not None else 0,
            created_at=row[4]
        ) for row in results
    ]

def get_score_details(db: Session, generated_image_id: int) -> ScoreInfo:
    """获取特定生成图片的详细评分信息"""
    result = db.execute(text("""
        SELECT 
            ie.id,
            ie.generated_image_id,
            ie.overall_score,
            ie.highlights,
            ie.ai_comment,
            ie.shooting_guidance,
            ie.created_at
        FROM image_evaluations ie
        WHERE ie.generated_image_id = :generated_image_id
    """), {"generated_image_id": generated_image_id}).fetchone()
    
    if not result:
        raise ValueError("未找到评分信息")
    
    return ScoreInfo(
        id=result[0],
        generated_image_id=result[1],
        overall_score=result[2],
        highlights=result[3],
        ai_comment=result[4],
        shooting_guidance=result[5],
        created_at=result[6]
    )
