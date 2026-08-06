from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import ProjectModule, ProjectPhase
from .serializers import ProjectModuleSerializer, ProjectPhaseSerializer


AUTHOR = {
    "name": "Santiago Vásquez Franco",
    "role": "Ingeniero de software",
    "bio": (
        "Creador de ConversationalBI. Construyendo herramientas de inteligencia "
        "conversacional para datos empresariales."
    ),
    "photo": "/author.jpg",
    "github": "https://github.com/xofranc",
    "linkedin": "https://www.linkedin.com/in/santiago-vasquez-franco-90aa6528b/",
    "email": "santiagofrancco3@gmail.com",
}


@api_view(['GET'])
@permission_classes([AllowAny])
def project_status(request):
    """Endpoint público con el estado del proyecto y roadmap."""
    phases = ProjectPhase.objects.all()
    modules = ProjectModule.objects.all()

    return Response({
        "project_name": "ConversationalBI",
        "tagline": "Hazle preguntas en lenguaje natural a tus datos.",
        "author": AUTHOR,
        "phases": ProjectPhaseSerializer(phases, many=True).data,
        "modules": ProjectModuleSerializer(modules, many=True).data,
        "live_url": "https://conversational-bi-eight.vercel.app/",
        "repo_url": "https://github.com/xofranc/conversationalBI",
    })
