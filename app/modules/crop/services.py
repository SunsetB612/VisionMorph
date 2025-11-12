"""
裁剪服务，集成 `crop_module/new_total.py` 中的核心流程。

主要职责：
- 调用 PanoramaCropper 生成裁剪候选图。
- 将裁剪结果保存到静态目录及数据库（temp_images、result_images）。
- 提供裁剪结果的查询接口。
"""
import importlib
import logging
import os
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import cv2
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.crop.schemas import (
    CropListResponse,
    CropRequest,
    CropResponse,
    CroppedImageInfo,
)
from app.modules.upload.services import UploadService

# ===== PanoramaCropper 懒加载配置 =====
NEW_TOTAL_DIR = os.path.join(settings.BASE_DIR, "crop_module")
if NEW_TOTAL_DIR not in sys.path:
    sys.path.insert(0, NEW_TOTAL_DIR)

try:
    import pandas as pd
except ImportError:  # pragma: no cover - 运行环境缺少 pandas
    pd = None  # type: ignore

logger = logging.getLogger(__name__)

_CROPPER_LOCK = threading.Lock()
_CROPPER_INSTANCE = None
_NEW_TOTAL_LOCK = threading.Lock()
_NEW_TOTAL_MODULE = None
_ANALYZER_LOCK = threading.Lock()
_ANALYZER_INSTANCE = None
_ANALYZER_LOAD_FAILED = False
_DOUBAO_LOCK = threading.Lock()
_DOUBAO_CLIENT = None
_DOUBAO_LOAD_FAILED = False


def _load_new_total_module():
    """
    懒加载 new_total 模块。
    """
    global _NEW_TOTAL_MODULE

    if _NEW_TOTAL_MODULE is None:
        with _NEW_TOTAL_LOCK:
            if _NEW_TOTAL_MODULE is None:
                try:
                    _NEW_TOTAL_MODULE = importlib.import_module("new_total")
                except ImportError as exc:
                    logger.error("加载 new_total 模块失败：%s", exc, exc_info=exc)
                    raise

    return _NEW_TOTAL_MODULE


def _get_composition_analyzer():
    """
    懒加载 MultimodalCompositionAnalyzer。
    """
    global _ANALYZER_INSTANCE, _ANALYZER_LOAD_FAILED

    if _ANALYZER_LOAD_FAILED:
        return None

    if _ANALYZER_INSTANCE is None:
        with _ANALYZER_LOCK:
            if _ANALYZER_INSTANCE is None and not _ANALYZER_LOAD_FAILED:
                try:
                    module = _load_new_total_module()
                    MultimodalCompositionAnalyzer = getattr(
                        module,
                        "MultimodalCompositionAnalyzer",
                    )
                    _ANALYZER_INSTANCE = MultimodalCompositionAnalyzer()
                except Exception as exc:  # pragma: no cover - 模型缺失等异常
                    _ANALYZER_LOAD_FAILED = True
                    logger.error("构图分析模型初始化失败：%s", exc, exc_info=exc)
                    return None

    return _ANALYZER_INSTANCE


def _get_doubao_client():
    """
    懒加载 DoubaoAPIClient。
    """
    global _DOUBAO_CLIENT, _DOUBAO_LOAD_FAILED

    if _DOUBAO_LOAD_FAILED or _DOUBAO_CLIENT is not None:
        return _DOUBAO_CLIENT

    if not settings.DOUBAO_API_KEY:
        _DOUBAO_LOAD_FAILED = True
        logger.warning("未配置 DOUBAO_API_KEY，跳过豆包拍摄建议生成")
        return None

    with _DOUBAO_LOCK:
        if _DOUBAO_CLIENT is None and not _DOUBAO_LOAD_FAILED:
            try:
                module = _load_new_total_module()
                DoubaoAPIClient = getattr(module, "DoubaoAPIClient")

                _DOUBAO_CLIENT = DoubaoAPIClient(
                    api_key=settings.DOUBAO_API_KEY,
                    model=settings.DOUBAO_MODEL_NAME,
                )
            except Exception as exc:  # pragma: no cover - 网络/依赖异常
                _DOUBAO_LOAD_FAILED = True
                logger.error("豆包客户端初始化失败：%s", exc, exc_info=exc)
                return None

    return _DOUBAO_CLIENT


def _read_direction_description(prompt_file_path: Optional[str]) -> str:
    """
    读取方位说明文本，支持 docx 与普通文本文件。
    """
    if not prompt_file_path:
        return "未提供方位说明"

    if not os.path.exists(prompt_file_path):
        return f"方位说明文件不存在：{prompt_file_path}"

    lower_path = prompt_file_path.lower()
    if lower_path.endswith(".docx"):
        try:
            module = _load_new_total_module()
            read_direction_desc = getattr(module, "read_direction_desc")
            return read_direction_desc(prompt_file_path)
        except Exception as exc:  # pragma: no cover - docx 解析异常
            logger.warning(
                "读取 docx 方位说明失败：%s，文件：%s",
                exc,
                prompt_file_path,
                exc_info=exc,
            )
            return f"方位说明读取失败：{exc}"

    try:
        with open(prompt_file_path, "r", encoding="utf-8") as file:
            return file.read() or "方位说明文件为空"
    except UnicodeDecodeError:
        try:
            with open(prompt_file_path, "r", encoding="gbk") as file:
                return file.read() or "方位说明文件为空"
        except Exception as exc:  # pragma: no cover - 非常规编码
            logger.warning(
                "读取方位说明文件失败：%s，文件：%s",
                exc,
                prompt_file_path,
                exc_info=exc,
            )
            return f"方位说明读取失败：{exc}"
    except Exception as exc:  # pragma: no cover - 其他异常
        logger.warning(
            "读取方位说明文件失败：%s，文件：%s",
            exc,
            prompt_file_path,
            exc_info=exc,
        )
        return f"方位说明读取失败：{exc}"


def _analyze_crop_image(image_np) -> Optional[Dict[str, str]]:
    """
    使用构图模型分析裁剪图。
    """
    analyzer = _get_composition_analyzer()
    if analyzer is None:
        return None

    try:
        return analyzer.analyze(image_np)
    except Exception as exc:  # pragma: no cover - 推理异常
        logger.warning("构图分析失败：%s", exc, exc_info=exc)
        return {"error": f"构图分析失败：{exc}"}


def _generate_doubao_suggestions(
    original_image,
    crop_image,
    region_type: str,
    coords_str: str,
    direction_desc: str,
) -> str:
    """
    调用豆包 API 生成拍摄建议。
    """
    client = _get_doubao_client()
    if client is None:
        return "豆包拍摄建议未启用"

    if original_image is None:
        return "原始图片读取失败，无法生成拍摄建议"

    try:
        return client.get_shooting_suggestions(
            original_img=original_image,
            crop_img=crop_image,
            region_type=region_type,
            coords=coords_str,
            direction_desc=direction_desc,
        )
    except Exception as exc:  # pragma: no cover - 网络/接口异常
        logger.warning("豆包拍摄建议生成失败：%s", exc, exc_info=exc)
        return f"豆包拍摄建议生成失败：{exc}"


def _ensure_dataframe(records: List[Dict[str, Any]]):
    """
    将记录转换为 pandas DataFrame。
    """
    if pd is None:
        raise RuntimeError("未安装 pandas，无法生成 Excel 报告")

    return pd.DataFrame(records)


def _write_excel_report(user_id: int, excel_dir: str, records: List[Dict[str, Any]]) -> str:
    """
    将裁剪结果写入/追加到用户 Excel 报告。
    """
    if not records:
        raise ValueError("没有可写入 Excel 的记录")

    os.makedirs(excel_dir, exist_ok=True)
    excel_path = os.path.join(excel_dir, f"user{user_id}_crop_report.xlsx")

    df_new = _ensure_dataframe(records)

    if os.path.exists(excel_path):
        try:
            df_existing = pd.read_excel(excel_path) if pd is not None else None
        except Exception as exc:  # pragma: no cover - 文件损坏等
            logger.warning("读取现有 Excel 失败，将覆盖写入：%s", exc, exc_info=exc)
            df_existing = None

        if df_existing is not None:
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
    else:
        df_combined = df_new

    df_combined.to_excel(excel_path, index=False)
    return excel_path


def _get_panorama_cropper():
    """
    懒加载 PanoramaCropper，避免在未触发裁剪时加载耗时模型。
    """
    global _CROPPER_INSTANCE

    if _CROPPER_INSTANCE is None:
        with _CROPPER_LOCK:
            if _CROPPER_INSTANCE is None:
                try:
                    module = _load_new_total_module()
                    PanoramaCropper = getattr(module, "PanoramaCropper")
                except Exception as exc:  # pragma: no cover
                    raise ValueError(f"裁剪模型加载失败: {exc}") from exc

                _CROPPER_INSTANCE = PanoramaCropper(
                    yolo_path=settings.YOLO_MODEL_PATH,
                )

    return _CROPPER_INSTANCE


# ===== 数据库辅助函数 =====
def _clear_previous_crops(db: Session, original_image_id: int) -> None:
    """
    清理旧的裁剪结果（view_angles 以 'result' 开头的记录）。
    """
    db.execute(
        text(
            """
            DELETE ri
            FROM result_images ri
            JOIN temp_images ti ON ri.temp_image_id = ti.id
            WHERE ti.original_image_id = :original_image_id
              AND ti.view_angles LIKE :prefix
            """,
        ),
        {
            "original_image_id": original_image_id,
            "prefix": "result%",
        },
    )

    db.execute(
        text(
            """
            DELETE FROM temp_images
            WHERE original_image_id = :original_image_id
              AND view_angles LIKE :prefix
            """,
        ),
        {
            "original_image_id": original_image_id,
            "prefix": "result%",
        },
    )


def _save_crop_to_storage(
    image_np,
    save_dir: str,
    filename: str,
) -> str:
    """
    将裁剪图保存到磁盘。
    """
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, filename)

    if not cv2.imwrite(file_path, image_np):  # pragma: no cover - 非常规失败
        raise ValueError(f"裁剪图片保存失败: {file_path}")

    return file_path


def _persist_crop_record(
    db: Session,
    original_image_id: int,
    filename: str,
    file_path: str,
    metadata: str,
    prompt_file_path: Optional[str] = None,
) -> Tuple[int, int]:
    """
    将裁剪结果写入 temp_images & result_images。

    返回:
        (result_image_id, temp_image_id)
    """
    temp_result = db.execute(
        text(
            """
            INSERT INTO temp_images (
                original_image_id,
                filename,
                file_path,
                view_angles,
                prompt_file_path,
                created_at
            )
            VALUES (
                :original_image_id,
                :filename,
                :file_path,
                :view_angles,
                :prompt_file_path,
                NOW()
            )
            """,
        ),
        {
            "original_image_id": original_image_id,
            "filename": filename,
            "file_path": file_path,
            "view_angles": metadata,
            "prompt_file_path": prompt_file_path,
        },
    )

    temp_image_id = temp_result.lastrowid
    if not temp_image_id:
        raise ValueError("数据库未能返回裁剪临时图片ID")

    result = db.execute(
        text(
            """
            INSERT INTO result_images (
                temp_image_id,
                filename,
                file_path,
                created_at
            )
            VALUES (
                :temp_image_id,
                :filename,
                :file_path,
                NOW()
            )
            """,
        ),
        {
            "temp_image_id": temp_image_id,
            "filename": filename,
            "file_path": file_path,
        },
    )

    result_image_id = result.lastrowid
    if not result_image_id:
        raise ValueError("数据库未能返回裁剪结果图片ID")

    return result_image_id, temp_image_id


# ===== 公共服务函数 =====
def create_crop_task(db: Session, request: CropRequest) -> CropResponse:
    """
    调用 PanoramaCropper 完成裁剪任务。
    """
    try:
        # 1. 查询原始图片及用户信息
        image_row = db.execute(
            text(
                """
                SELECT id, filename, file_path, user_id
                FROM images
                WHERE id = :image_id
                """,
            ),
            {"image_id": request.original_image_id},
        ).fetchone()

        if not image_row:
            raise ValueError("原始图片不存在")

        original_image_id, original_filename, original_file_path, user_id = image_row

        # 2. 准备输出目录 & 清理旧数据
        dirs = UploadService.create_user_directories(user_id)
        results_dir = dirs["results_dir"]
        excel_dir = dirs["excel_dir"]
        _clear_previous_crops(db, original_image_id)

        # 3. 获取候选生成图片
        if not request.use_generated_images:
            raise ValueError("当前裁剪服务仅支持基于生成图片进行裁剪")

        candidate_limit = max(request.top_n * 3, request.top_n, 10)
        generated_rows = db.execute(
            text(
                """
                SELECT 
                    ti.id,
                    ti.filename,
                    ti.file_path,
                    ti.view_angles,
                    ti.prompt_file_path,
                    COALESCE(ie.overall_score, 0) AS overall_score,
                    ti.created_at
                FROM temp_images ti
                LEFT JOIN image_evaluations ie ON ti.id = ie.generated_image_id
                WHERE ti.original_image_id = :original_image_id
                  AND (ti.view_angles IS NULL OR ti.view_angles NOT LIKE :result_prefix)
                ORDER BY COALESCE(ie.overall_score, 0) DESC, ti.created_at DESC
                LIMIT :limit
                """,
            ),
            {
                "original_image_id": original_image_id,
                "result_prefix": "result%",
                "limit": candidate_limit,
            },
        ).fetchall()

        if not generated_rows:
            raise ValueError("未找到可用于裁剪的生成图片")

        # 4. 载入裁剪模型
        cropper = _get_panorama_cropper()
        original_image_np = None
        if os.path.exists(original_file_path):
            original_image_np = cv2.imread(original_file_path)
            if original_image_np is None:  # pragma: no cover - 读取失败
                logger.warning("原始图片读取失败：%s", original_file_path)
        else:
            logger.warning("原始图片不存在：%s", original_file_path)
        max_top_n = min(request.top_n, settings.MAX_CROP_TOP_N)

        batch_ts = int(time.time() * 1000)
        saved_count = 0
        excel_records: List[Dict[str, Any]] = []
        direction_desc_cache: Dict[str, str] = {}

        for generated in generated_rows:
            (
                generated_image_id,
                generated_filename,
                generated_file_path,
                _view_angles,
                prompt_file_path,
                _overall_score,
                _created_at,
            ) = generated

            if not os.path.exists(generated_file_path):
                continue

            image_np = cv2.imread(generated_file_path)
            if image_np is None:
                continue

            remaining_slots = max_top_n - saved_count
            if remaining_slots <= 0:
                break

            direction_desc_key = prompt_file_path or f"generated-{generated_image_id}"
            if direction_desc_key not in direction_desc_cache:
                direction_desc_cache[direction_desc_key] = _read_direction_description(
                    prompt_file_path,
                )
            direction_description = direction_desc_cache[direction_desc_key]

            if request.method:
                regions, _, _ = cropper.get_potential_regions(
                    image_np,
                    method=request.method,
                )
                cropped_regions = cropper.crop_regions(
                    image_np,
                    regions,
                    top_n=remaining_slots,
                )
            else:
                process_result = cropper.process_panorama(
                    image_path=generated_file_path,
                    top_n=remaining_slots,
                )
                cropped_regions = process_result.get("cropped_regions", [])

            for index, (crop_img, region_type, coords) in enumerate(cropped_regions, start=1):
                filename = (
                    f"{os.path.splitext(generated_filename)[0]}_result_"
                    f"{batch_ts}_{generated_image_id}_{saved_count + 1}.jpg"
                )
                result_file_path = _save_crop_to_storage(crop_img, results_dir, filename)

                coords_str = ",".join(map(str, coords))
                metadata = (
                    f"result:generated:{generated_image_id}:{region_type}:{coords_str}"
                )

                result_image_id, temp_image_id = _persist_crop_record(
                    db=db,
                    original_image_id=original_image_id,
                    filename=filename,
                    file_path=result_file_path,
                    metadata=metadata,
                    prompt_file_path=prompt_file_path,
                )

                analysis_result = _analyze_crop_image(crop_img)
                if analysis_result and "error" in analysis_result:
                    composition_score = ""
                    style_labels = ""
                    analysis_explanation = analysis_result["error"]
                    analysis_suggestions = ""
                elif analysis_result:
                    composition_score = analysis_result.get("composition_score", "")
                    style_labels = ", ".join(analysis_result.get("style_labels", []))
                    analysis_explanation = analysis_result.get("explanation", "")
                    analysis_suggestions = "\n".join(
                        analysis_result.get("suggestions", []),
                    )
                else:
                    composition_score = ""
                    style_labels = ""
                    analysis_explanation = "构图分析未启用"
                    analysis_suggestions = ""

                doubao_suggestions = _generate_doubao_suggestions(
                    original_image=original_image_np,
                    crop_image=crop_img,
                    region_type=region_type,
                    coords_str=coords_str,
                    direction_desc=direction_description,
                )

                excel_records.append(
                    {
                        "original_image_id": original_image_id,
                        "generated_image_id": generated_image_id,
                        "result_image_id": result_image_id,
                        "temp_image_id": temp_image_id,
                        "generated_filename": generated_filename,
                        "result_filename": filename,
                        "result_file_path": result_file_path,
                        "region_type": region_type,
                        "coords": coords_str,
                        "metadata": metadata,
                        "composition_score": composition_score,
                        "style_labels": style_labels,
                        "analysis_explanation": analysis_explanation,
                        "analysis_suggestions": analysis_suggestions,
                        "doubao_shooting_suggestions": doubao_suggestions,
                        "direction_description": direction_description,
                        "prompt_file_path": prompt_file_path or "",
                        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
                    },
                )

                saved_count += 1
                if saved_count >= max_top_n:
                    break

            if saved_count >= max_top_n:
                break

        if saved_count == 0:
            raise ValueError("未能基于生成图片生成裁剪结果")

        if excel_records:
            excel_path = _write_excel_report(user_id, excel_dir, excel_records)
            logger.info(
                "已生成用户 %s 的裁剪分析报告：%s（新增 %s 条记录）",
                user_id,
                excel_path,
                len(excel_records),
            )

        db.commit()

        return CropResponse(
            original_image_id=original_image_id,
            cropped_count=saved_count,
            message=f"成功生成 {saved_count} 张裁剪图",
        )

    except Exception as exc:
        db.rollback()
        if isinstance(exc, ValueError):
            raise exc
        raise ValueError(f"裁剪任务失败: {exc}") from exc


def get_crops_by_original_image(db: Session, original_image_id: int) -> CropListResponse:
    """
    查询某张原始图片的裁剪结果。
    """
    rows = db.execute(
        text(
            """
            SELECT
                ri.id,
                ri.temp_image_id,
                ri.filename,
                ri.file_path,
                ri.created_at
            FROM result_images ri
            JOIN temp_images ti ON ri.temp_image_id = ti.id
            WHERE ti.original_image_id = :original_image_id
              AND ti.view_angles LIKE :prefix
            ORDER BY ri.created_at DESC
            """,
        ),
        {
            "original_image_id": original_image_id,
            "prefix": "result%",
        },
    ).fetchall()

    crops: List[CroppedImageInfo] = [
        CroppedImageInfo(
            id=row[0],
            temp_image_id=row[1],
            filename=row[2],
            file_path=row[3],
            created_at=row[4],
        )
        for row in rows
    ]

    return CropListResponse(
        original_image_id=original_image_id,
        total_count=len(crops),
        crops=crops,
    )


