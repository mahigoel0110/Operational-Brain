from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def home():
    return {
        "message": "Operational Brain Backend Running 🚀"
    }


from app.schemas.health import HealthResponse


@router.get(
    "/health",
    response_model=HealthResponse
)
def health():

    return HealthResponse(
        status="healthy"
    )