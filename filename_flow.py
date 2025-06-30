import re

from pocketflow import Flow, Node


class FilenameNode(Node):
    def prep(self, shared):
        return shared["user_input"].get("natural_language", "documentation")

    def exec(self, natural_language):
        # 简单 slugify: 只保留中文字符、字母数字和空格，空格转横线，小写
        slug: str = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fa5 ]", "", natural_language)
        slug = slug.strip().lower().replace(" ", "-")[:10]
        print(f"filename_flow: slug: {slug}")
        if not slug:
            slug = "documentation"
        return slug + ".md"

    def post(self, shared, prep_res, exec_res):
        shared["generated_filename"] = exec_res
        return "default"


def create_filename_flow():
    node = FilenameNode()
    return Flow(start=node)
