import gzip
from pathlib import Path

from app.services.dump import parse

DUMP = """\
CREATE TABLE `flarum_tags` (
  `id` int(10) unsigned NOT NULL,
  `name` varchar(64) NOT NULL,
  `slug` varchar(64) NOT NULL
) ENGINE=InnoDB;

INSERT INTO `flarum_tags` VALUES (1,'General','general'),(2,'tea','tea');
"""


def test_parse_tables(tmp_path: Path) -> None:
    path = tmp_path / "t.sql.gz"
    path.write_bytes(gzip.compress(DUMP.encode()))
    data = parse(str(path), {"flarum_tags"})
    cols, rows = data["flarum_tags"]
    assert cols == ["id", "name", "slug"]
    assert rows[1] == ["2", "tea", "tea"]


def test_escapes_and_null(tmp_path: Path) -> None:
    dumped = DUMP + "\nINSERT INTO `flarum_tags` VALUES (3,'a\\'b','x\\\\y'),(4,NULL,NULL);\n"
    path = tmp_path / "t.sql.gz"
    path.write_bytes(gzip.compress(dumped.encode()))
    rows = parse(str(path), {"flarum_tags"})["flarum_tags"][1]
    assert rows[2] == ["3", "a'b", "x\\y"]
    assert rows[3] == ["4", None, None]
