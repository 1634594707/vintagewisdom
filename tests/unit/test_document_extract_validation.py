from pathlib import Path

import pytest

from vintagewisdom.cli.commands import _validate_extracted_document_text as cli_validate
from vintagewisdom.web.app import _validate_extracted_document_text as web_validate


def test_document_validation_allows_normal_text() -> None:
    text = "决策节点：先小范围试导入，再逐步扩大范围。"
    cli_validate(text, Path("ok.docx"))
    web_validate(text, Path("ok.docx"))


def test_document_validation_rejects_garbled_text() -> None:
    garbled = "????????\n????????????????\n??????"
    with pytest.raises(RuntimeError, match="looks corrupted"):
        cli_validate(garbled, Path("broken.docx"))
    with pytest.raises(RuntimeError, match="looks corrupted"):
        web_validate(garbled, Path("broken.docx"))
