from pydantic import BaseModel, Field


class ErrorSchema(BaseModel):
    """Mensagem de erro retornada pela API."""

    message: str = Field(
        ...,
        description="Mensagem legível explicando o erro ocorrido.",
        example="Atividade não encontrada.",
    )

    model_config = {
        "openapi_extra": {
            "description": "Resposta padrão para erros de validação, busca ou persistência.",
            "example": {
                "message": "Atividade não encontrada.",
            },
        }
    }
