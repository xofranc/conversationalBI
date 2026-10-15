import pytest

from apps.queries.application.dtos import (
    AIQueryRequestDTO,
    AnalysisQueryRequestDTO,
    ChartSelectionDTO,
    EngineResultDTO,
    SQLExecutionResultDTO,
    StatisticalCalculationResultDTO,
)
from apps.queries.application.execute_statistical_analysis import ExecuteStatisticalAnalysis
from apps.queries.application.generate_ai_query import GenerateAIQuery
from apps.queries.application.ports import SQLSafetyViolation, UnsupportedStatisticalAnalysis
from apps.queries.domain.policies import SQLSafetyPolicy


SCHEMA = {"tables": [{"name": "sales", "columns": [{"name": "amount"}]}]}
AI_REQUEST = AIQueryRequestDTO(
    question="total sales?", dataset_id=7, schema=SCHEMA, history=(),
)
ANALYSIS_REQUEST = AnalysisQueryRequestDTO(
    intent="summary", dataset_id=7, question="summarize sales", schema=SCHEMA,
)


class PromptFake:
    def __init__(self):
        self.initial = []
        self.corrections = []
        self.empty_results = []

    def compose(self, request):
        self.initial.append(request)
        return "initial prompt"

    def build_correction(self, question, schema, previous_sql, error):
        self.corrections.append((question, schema, previous_sql, error))
        return "correction prompt"

    def build_empty_result(self, question, schema, previous_sql):
        self.empty_results.append((question, schema, previous_sql))
        return "empty-result prompt"


class GeneratorFake:
    def __init__(self, *sql_values):
        self.sql_values = list(sql_values)
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        value = self.sql_values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


class SafetyFake:
    def __init__(self, violation=None):
        self.violation = violation
        self.validated = []

    def validate(self, sql):
        self.validated.append(sql)
        if self.violation:
            raise self.violation


class ExecutorFake:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def execute(self, dataset_id, sql):
        self.calls.append((dataset_id, sql))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class ChartFake:
    def __init__(self):
        self.calls = []

    def select(self, columns, rows):
        self.calls.append((columns, rows))
        return ChartSelectionDTO("bar", {"xKey": "region"})


class AnswerFake:
    def __init__(self, answer="answer"):
        self.answer = answer
        self.calls = []

    def write(self, *args):
        self.calls.append(args)
        return self.answer


class SuggestionsFake:
    def __init__(self, values=("try amount",)):
        self.values = tuple(values)
        self.schemas = []

    def suggest(self, schema):
        self.schemas.append(schema)
        return self.values


def make_ai_engine(*, sql_values, execution_results=(), violation=None, safety_policy=None):
    prompts = PromptFake()
    generator = GeneratorFake(*sql_values)
    safety = SafetyFake(violation)
    executor = ExecutorFake(*execution_results)
    charts, answers, suggestions = ChartFake(), AnswerFake(), SuggestionsFake()
    engine = GenerateAIQuery(
        prompts, generator, safety, executor, charts, answers, suggestions,
        **({} if safety_policy is None else {"safety_policy": safety_policy}),
    )
    return engine, prompts, generator, safety, executor, charts, answers, suggestions


def test_generate_ai_query_uses_three_policy_attempts_and_returns_final_failure():
    engine, prompts, generator, _safety, _executor, charts, answers, suggestions = make_ai_engine(
        sql_values=[RuntimeError("bad sql"), RuntimeError("still bad"), RuntimeError("last failure")],
    )

    result = engine.execute(AI_REQUEST)

    assert not result.success
    assert result.retry_count == 3
    assert result.error_message == "last failure"
    assert len(generator.prompts) == 3
    assert generator.prompts == ["initial prompt", "correction prompt", "correction prompt"]
    assert prompts.corrections == [
        (AI_REQUEST.question, SCHEMA, "", "bad sql"),
        (AI_REQUEST.question, SCHEMA, "", "still bad"),
        (AI_REQUEST.question, SCHEMA, "", "last failure"),
    ]
    assert result.suggestions == ("try amount",)
    assert suggestions.schemas == [SCHEMA]
    assert not charts.calls and not answers.calls


def test_generate_ai_query_retries_empty_result_then_builds_chart_and_answer():
    rows = ({"region": "Bogota", "total": 12},)
    columns = ({"name": "region", "dtype": "str"}, {"name": "total", "dtype": "int"})
    engine, prompts, generator, safety, executor, charts, answers, suggestions = make_ai_engine(
        sql_values=["SELECT region, SUM(total) FROM sales", "SELECT region, SUM(total) FROM sales"],
        execution_results=[SQLExecutionResultDTO((), columns), SQLExecutionResultDTO(rows, columns)],
    )

    result = engine.execute(AI_REQUEST)

    assert result.success and result.retry_count == 1
    assert result.rows == rows and result.columns == columns
    assert result.chart_type == "bar" and result.chart_config == {"xKey": "region"}
    assert result.answer == "answer"
    assert prompts.empty_results == [(AI_REQUEST.question, SCHEMA, "SELECT region, SUM(total) FROM sales")]
    assert generator.prompts == ["initial prompt", "empty-result prompt"]
    assert safety.validated == [call[1] for call in executor.calls]
    assert executor.calls == [
        (7, "SELECT region, SUM(total) FROM sales"),
        (7, "SELECT region, SUM(total) FROM sales"),
    ]
    assert charts.calls == [(columns, rows)]
    assert answers.calls == [(AI_REQUEST.question, executor.calls[-1][1], rows, 1)]
    assert not suggestions.schemas


def test_generate_ai_query_unsafe_sql_fails_fast_without_execution_or_retry():
    engine, _prompts, generator, safety, executor, charts, answers, suggestions = make_ai_engine(
        sql_values=["DROP TABLE sales", "SELECT 1"],
        violation=SQLSafetyViolation("unsafe SQL"),
        safety_policy=SQLSafetyPolicy(security_rejection_is_retryable=False),
    )

    result = engine.execute(AI_REQUEST)

    assert not result.success and result.error_message == "unsafe SQL"
    assert result.retry_count == 0 and generator.prompts == ["initial prompt"]
    assert safety.validated == ["DROP TABLE sales"]
    assert not executor.calls and not charts.calls and not answers.calls
    assert result.suggestions == ("try amount",) and suggestions.schemas == [SCHEMA]


def test_generate_ai_query_retries_security_rejection_only_when_policy_allows_it():
    class RejectFirstSQL:
        def __init__(self):
            self.validated = []

        def validate(self, sql):
            self.validated.append(sql)
            if len(self.validated) == 1:
                raise SQLSafetyViolation("unsafe SQL")

    prompts = PromptFake()
    generator = GeneratorFake("DROP TABLE sales", "SELECT amount FROM sales")
    safety = RejectFirstSQL()
    executor = ExecutorFake(SQLExecutionResultDTO(
        ({"amount": 12},), ({"name": "amount", "dtype": "int"},),
    ))
    charts, answers, suggestions = ChartFake(), AnswerFake(), SuggestionsFake()
    engine = GenerateAIQuery(
        prompts,
        generator,
        safety,
        executor,
        charts,
        answers,
        suggestions,
        safety_policy=SQLSafetyPolicy(security_rejection_is_retryable=True),
    )

    result = engine.execute(AI_REQUEST)

    assert result.success and result.retry_count == 1
    assert generator.prompts == ["initial prompt", "correction prompt"]
    assert prompts.corrections == [
        (AI_REQUEST.question, SCHEMA, "DROP TABLE sales", "unsafe SQL"),
    ]
    assert safety.validated == ["DROP TABLE sales", "SELECT amount FROM sales"]
    assert executor.calls == [(7, "SELECT amount FROM sales")]
    assert not suggestions.schemas


class CalculatorFake:
    def __init__(self, outcome):
        self.outcome = outcome
        self.requests = []

    def calculate(self, request):
        self.requests.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class StatisticalAnswerFake:
    def __init__(self):
        self.calls = []

    def write(self, *args):
        self.calls.append(args)
        return "statistical answer"


def test_statistical_analysis_success_comments_method_and_writes_answer():
    rows = ({"column": "amount", "mean": 5},)
    columns = ({"name": "mean", "dtype": "int"},)
    calculator = CalculatorFake(StatisticalCalculationResultDTO(
        method="descriptive statistics", rows=rows, columns=columns,
        chart_type="table", chart_config={"xKey": "column"},
    ))
    answers, suggestions = StatisticalAnswerFake(), SuggestionsFake()
    use_case = ExecuteStatisticalAnalysis(calculator, answers, suggestions)

    result = use_case.execute(ANALYSIS_REQUEST)

    assert result.success and result.sql == "-- descriptive statistics"
    assert result.answer == "statistical answer" and result.rows == rows
    assert result.columns == columns
    assert result.chart_type == "table" and result.chart_config == {"xKey": "column"}
    assert result.model_used == "análisis:summary"
    assert calculator.requests[0].intent == "summary"
    assert answers.calls == [(ANALYSIS_REQUEST.question, "-- descriptive statistics", rows, 1)]
    assert not suggestions.schemas


def test_statistical_analysis_preserves_supported_error_and_uses_suggestions():
    suggestions = SuggestionsFake(("use a date column",))
    use_case = ExecuteStatisticalAnalysis(
        CalculatorFake(UnsupportedStatisticalAnalysis("faltan fechas")),
        StatisticalAnswerFake(),
        suggestions,
    )

    result = use_case.execute(ANALYSIS_REQUEST)

    assert not result.success and result.error_message == "faltan fechas"
    assert result.suggestions == ("use a date column",)
    assert suggestions.schemas == [SCHEMA]
    assert result.model_used == "análisis:summary"


def test_statistical_analysis_hides_unexpected_error_details():
    use_case = ExecuteStatisticalAnalysis(
        CalculatorFake(RuntimeError("database secret")),
        StatisticalAnswerFake(),
        SuggestionsFake(()),
    )

    result = use_case.execute(ANALYSIS_REQUEST)

    assert not result.success
    assert result.error_message == ExecuteStatisticalAnalysis.UNEXPECTED_FAILURE_MESSAGE
    assert "database secret" not in result.error_message
