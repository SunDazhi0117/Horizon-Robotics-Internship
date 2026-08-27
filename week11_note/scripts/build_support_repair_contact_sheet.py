"""Build Week11 overview images used for structural-support review."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
SCENES = (
    ("Pantry: fridge to cupboard", "pantry_fridge_to_cupboard.gif"),
    ("Workshop: drawer to locker", "workshop_drawer_to_locker.gif"),
    ("Laundry: washer to dryer", "laundry_washer_to_dryer.gif"),
    ("Laboratory: incubator to cold storage", "laboratory_incubator_to_cold_storage.gif"),
    ("Printer: panel and tray restore", "printer_service_panel_tray_restore.gif"),
    ("Sterilizer: latch, panel, and tray reset", "sterilizer_safety_latch_panel_tray_reset.gif"),
)


def _frame(path: Path, *, final: bool) -> Image.Image:
    image = Image.open(path)
    if final:
        image.seek(image.n_frames - 1)
    return image.convert("RGB")


def _tile(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)


def _overview() -> None:
    tile_size = (480, 340)
    title_height = 42
    label_height = 30
    canvas = Image.new("RGB", (tile_size[0] * 3, title_height + (tile_size[1] + label_height) * 2), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((16, 14), "Week11 after structural-support repair — initial state", fill="black", font=font)
    for index, (label, filename) in enumerate(SCENES):
        column = index % 3
        row = index // 3
        x = column * tile_size[0]
        y = title_height + row * (tile_size[1] + label_height)
        canvas.paste(_tile(_frame(ASSET_DIR / filename, final=False), tile_size), (x, y))
        draw.text((x + 10, y + tile_size[1] + 9), label, fill="black", font=font)
    canvas.save(ASSET_DIR / "week11_all_scenes_after_support_repair.png")


def _initial_final_review() -> None:
    tile_size = (520, 370)
    title_height = 50
    row_label_height = 28
    row_height = tile_size[1] + row_label_height
    canvas = Image.new("RGB", (tile_size[0] * 2, title_height + row_height * len(SCENES)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((16, 12), "Week11 structural-support review", fill="black", font=font)
    draw.text((220, 32), "Initial", fill="black", font=font)
    draw.text((740, 32), "Final", fill="black", font=font)
    for row, (label, filename) in enumerate(SCENES):
        y = title_height + row * row_height
        path = ASSET_DIR / filename
        canvas.paste(_tile(_frame(path, final=False), tile_size), (0, y))
        canvas.paste(_tile(_frame(path, final=True), tile_size), (tile_size[0], y))
        draw.rectangle((0, y + tile_size[1], tile_size[0] * 2, y + row_height), fill="white")
        draw.text((12, y + tile_size[1] + 8), label, fill="black", font=font)
    canvas.save(ASSET_DIR / "week11_support_repair_initial_final_review.png")


def _timeline(gif_name: str, output_name: str, stages: tuple[tuple[str, float], ...]) -> None:
    image = Image.open(ASSET_DIR / gif_name)
    width, height = image.size
    label_height = 28
    canvas = Image.new("RGB", (width, (height + label_height) * len(stages)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for row, (label, fraction) in enumerate(stages):
        frame_index = round((image.n_frames - 1) * fraction)
        image.seek(frame_index)
        y = row * (height + label_height)
        canvas.paste(image.convert("RGB"), (0, y))
        draw.text((12, y + height + 8), label, fill="black", font=font)
    canvas.save(ASSET_DIR / output_name)


if __name__ == "__main__":
    _overview()
    _initial_final_review()
    printer_stages = (
        ("Initial", 0.0),
        ("Service panel open", 0.24),
        ("Toner tray extended", 0.46),
        ("Panel closing", 0.84),
        ("Restored", 1.0),
    )
    sterilizer_stages = (
        ("Initial and locked", 0.0),
        ("Safety latch unlocked", 0.14),
        ("Service panel open", 0.34),
        ("Instrument tray extended", 0.48),
        ("Panel closing", 0.72),
        ("Latch relocked", 0.94),
        ("Restored", 1.0),
    )
    _timeline(
        "printer_service_panel_tray_restore.gif",
        "printer_service_panel_tray_restore_contact_sheet.png",
        printer_stages,
    )
    _timeline(
        "printer_service_panel_tray_restore_top_view.gif",
        "printer_service_panel_tray_restore_top_contact_sheet.png",
        printer_stages,
    )
    _timeline(
        "sterilizer_safety_latch_panel_tray_reset.gif",
        "sterilizer_safety_latch_panel_tray_reset_contact_sheet.png",
        sterilizer_stages,
    )
    _timeline(
        "sterilizer_safety_latch_panel_tray_reset_top_view.gif",
        "sterilizer_safety_latch_panel_tray_reset_top_contact_sheet.png",
        sterilizer_stages,
    )
