class NodeClassifier:

    IGNORE = [
        ".git/",
        ".idea/",
        ".venv/",
        ".pytest_cache/",
        ".opencode/",
        ".obsidian/",
        "graphify-out/",
        "vault/",
    ]

    @staticmethod
    def should_ignore(node):

        source = node.get("source_file", "").replace("\\", "/")

        for ignore in NodeClassifier.IGNORE:
            if ignore in source:
                return True

        return False

    @staticmethod
    def classify(node):

        source = node.get("source_file", "").replace("\\", "/")

        if "/models" in source:
            return "Models"

        if "/services" in source:
            return "Services"

        if "/views" in source:
            return "Views"

        if "/serializers" in source:
            return "Serializers"

        if "/tests" in source:
            return "Tests"

        if "/migrations" in source:
            return "Migrations"

        if "/config" in source:
            return "Config"

        if "/frontend" in source:
            return "Frontend"

        if "/infra" in source:
            return "Infrastructure"

        return "Misc"