from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.incidentes import CorrelacionarResponseModel
from services.incidentes_service import dados_incidentes, correlacionar_incidentes_entidades

router = APIRouter()

@router.post(
    "/correlacionar",
    response_model=CorrelacionarResponseModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Força a correlação de incidentes com entidades do New Relic",
    description="Força a correlação de incidentes com entidades do New Relic, atualizando os dados em memória e persistindo no cache. Sempre retorna dados reais, nunca simulados.",
)
async def correlacionar_incidentes():
    try:
        await correlacionar_incidentes_entidades()
        total_incidentes = len(dados_incidentes.get("incidentes", []))
        total_entidades_associadas = sum(len(v) for v in dados_incidentes.get("entidades_associadas", {}).values())
        return CorrelacionarResponseModel(
            mensagem="Correlação de incidentes concluída",
            total_incidentes=total_incidentes,
            total_entidades_associadas=total_entidades_associadas,
            timestamp=datetime.now().isoformat(),
            explicacao="Este endpoint força a correlação entre incidentes e entidades do New Relic, atualizando os dados em memória.",
            sugestao="Utilize este recurso após inserir novos incidentes ou entidades para garantir que as análises estejam atualizadas.",
            proximos_passos="Após a correlação, revise os incidentes e entidades para validar se as associações estão corretas."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao correlacionar incidentes: {e}")
