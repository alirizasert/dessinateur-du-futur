QWEN_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
GLM_DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"


def default_base_url(provider: str) -> str:
    name = (provider or "").lower()
    if name == "glm":
        return GLM_DEFAULT_BASE_URL
    return QWEN_DEFAULT_BASE_URL

