"""REST adapter for the project status read use case."""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

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


class ProjectStatusView(APIView):
    permission_classes = [AllowAny]
    pagination_class = None
    use_cases = None

    def get(self, request):
        status_dto = self.use_cases["get_status"].execute()
        return Response({
            "project_name": "ConversationalBI",
            "tagline": "Hazle preguntas en lenguaje natural a tus datos.",
            "author": AUTHOR,
            "phases": ProjectPhaseSerializer(status_dto.phases, many=True).data,
            "modules": ProjectModuleSerializer(status_dto.modules, many=True).data,
            "live_url": "https://conversational-bi-eight.vercel.app/",
            "repo_url": "https://github.com/xofranc/conversationalBI",
        })
