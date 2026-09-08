"""Audio and pasted scripts must not be judged on camera / shots."""

from __future__ import annotations

import unittest

from diagnosis import (
    _VISUAL_TERMS,
    diagnose_prompt,
    local_fallback_diagnose,
    scrub_visual_advice,
)
from media import media_kind


def _advice_blob(data: dict) -> str:
    parts = [
        data.get("priority", ""),
        data.get("hook", {}).get("advice", ""),
        data.get("homogeneity", {}).get("advice", ""),
        data.get("cta", {}).get("advice", ""),
        data.get("retention", {}).get("advice", ""),
    ]
    return "".join(str(p) for p in parts)


class MediaKindTests(unittest.TestCase):
    def test_filename_kinds(self):
        self.assertEqual(media_kind(None), "script")
        self.assertEqual(media_kind(""), "script")
        self.assertEqual(media_kind("clip.m4a"), "audio")
        self.assertEqual(media_kind("voice.MP3"), "audio")
        self.assertEqual(media_kind("take.mp4"), "video")
        self.assertEqual(media_kind("take.MOV"), "video")

    def test_prompt_forbids_shots_on_audio_and_script(self):
        for kind in ("audio", "script"):
            prompt = diagnose_prompt(kind)
            self.assertIn("没有镜头", prompt)
            self.assertIn("严禁", prompt)
            self.assertNotIn("可以评价镜头", prompt)

    def test_prompt_allows_shots_on_video(self):
        prompt = diagnose_prompt("video")
        self.assertIn("可以评价镜头", prompt)

    def test_local_fallback_audio_has_no_visual_terms(self):
        script = "这款面膜才九十九，快来买，限时优惠。"
        for kind in ("audio", "script"):
            data = local_fallback_diagnose(script, kind)
            blob = _advice_blob(data)
            for term in _VISUAL_TERMS:
                self.assertNotIn(term, blob, f"{kind} advice still has {term!r}: {blob}")

    def test_local_fallback_video_may_mention_shots(self):
        script = "这款面膜才九十九，快来买。"
        data = local_fallback_diagnose(script, "video")
        blob = _advice_blob(data)
        self.assertTrue(
            any(term in blob for term in ("镜头", "出镜", "画面")),
            blob,
        )

    def test_scrub_strips_model_shot_advice(self):
        dirty = {
            "hook": {"score": "低", "advice": "前三秒加反差画面和镜头切换。"},
            "homogeneity": {"score": "高", "advice": "增加人物出镜。"},
            "cta": {"has_cta": False, "advice": "结尾引导到店。"},
            "retention": {"score": "中", "advice": "中段切镜太少。"},
            "priority": "先改镜头节奏",
        }
        cleaned = scrub_visual_advice(dirty, "audio")
        blob = _advice_blob(cleaned)
        for term in _VISUAL_TERMS:
            self.assertNotIn(term, blob, blob)
        untouched = scrub_visual_advice(
            {"hook": {"score": "低", "advice": "加一个镜头切换。"}, "homogeneity": {}, "cta": {}, "retention": {}, "priority": ""},
            "video",
        )
        self.assertIn("镜头", untouched["hook"]["advice"])


if __name__ == "__main__":
    unittest.main()
