"""Repositorios ORM de historial, resultados y feedback."""

from __future__ import annotations

from apps.queries.domain.entities import QueryFeedback as FeedbackEntity
from apps.queries.domain.entities import QueryHistory as HistoryEntity
from apps.queries.domain.entities import QueryResult as ResultEntity
from apps.queries.domain.repositories import (
    QueryFeedbackRepository,
    QueryHistoryRepository,
    QueryResultRepository,
)
from apps.queries.domain.value_objects import ChartType, FeedbackScore

from .models import QueryFeedback as FeedbackModel
from .models import QueryHistory as HistoryModel
from .models import QueryResult as ResultModel


def _history_entity(model: HistoryModel) -> HistoryEntity:
    return HistoryEntity(
        id=model.pk,
        user_id=model.user_id,
        dataset_id=model.dataset_id,
        question=model.question,
        sql_generated=model.sql_generated,
        execution_time=model.execution_time,
        success=model.success,
        error_msg=model.error_msg,
        model_used=model.model_used,
        retry_count=model.retry_count,
        cached=model.cached,
        created_at=model.created_at,
    )


def _result_entity(model: ResultModel) -> ResultEntity:
    return ResultEntity(
        id=model.pk,
        query_id=model.query_id,
        result_json=model.result_json,
        columns=model.columns,
        row_count=model.row_count,
        answer=model.answer,
        chart_type=ChartType(model.chart_type),
        chart_config=model.chart_config,
    )


def _feedback_entity(model: FeedbackModel) -> FeedbackEntity:
    return FeedbackEntity(
        id=model.pk,
        query_id=model.query_id,
        score=FeedbackScore(model.score),
        comment=model.comment,
        created_at=model.created_at,
    )


class DjangoQueryHistoryRepository(QueryHistoryRepository):
    def get_by_id(self, query_id: int) -> HistoryEntity | None:
        model = HistoryModel.objects.filter(pk=query_id).first()
        return _history_entity(model) if model is not None else None

    def list_by_user(self, user_id: int) -> tuple[HistoryEntity, ...]:
        return tuple(_history_entity(model) for model in HistoryModel.objects.filter(user_id=user_id))

    def list_by_dataset(self, dataset_id: int) -> tuple[HistoryEntity, ...]:
        return tuple(
            _history_entity(model) for model in HistoryModel.objects.filter(dataset_id=dataset_id)
        )

    def save(self, query: HistoryEntity) -> HistoryEntity:
        values = {
            "user_id": query.user_id,
            "dataset_id": query.dataset_id,
            "question": query.question,
            "sql_generated": query.sql_generated,
            "execution_time": query.execution_time,
            "success": query.success,
            "error_msg": query.error_msg,
            "model_used": query.model_used,
            "retry_count": query.retry_count,
            "cached": query.cached,
        }
        if query.id is None:
            model = HistoryModel.objects.create(**values)
        else:
            model, _ = HistoryModel.objects.update_or_create(pk=query.id, defaults=values)
        return _history_entity(model)


class DjangoQueryResultRepository(QueryResultRepository):
    def get_by_query_id(self, query_id: int) -> ResultEntity | None:
        model = ResultModel.objects.filter(query_id=query_id).first()
        return _result_entity(model) if model is not None else None

    def save(self, result: ResultEntity) -> ResultEntity:
        values = {
            "result_json": result.result_json,
            "columns": result.columns,
            "row_count": result.row_count,
            "answer": result.answer,
            "chart_type": result.chart_type.value,
            "chart_config": result.chart_config,
        }
        if result.id is not None:
            model, _ = ResultModel.objects.update_or_create(
                pk=result.id, defaults={"query_id": result.query_id, **values}
            )
        else:
            model, _ = ResultModel.objects.update_or_create(
                query_id=result.query_id, defaults=values
            )
        return _result_entity(model)


class DjangoQueryFeedbackRepository(QueryFeedbackRepository):
    def get_by_query_id(self, query_id: int) -> FeedbackEntity | None:
        model = FeedbackModel.objects.filter(query_id=query_id).first()
        return _feedback_entity(model) if model is not None else None

    def save(self, feedback: FeedbackEntity) -> FeedbackEntity:
        values = {"score": int(feedback.score), "comment": feedback.comment}
        if feedback.id is not None:
            model, _ = FeedbackModel.objects.update_or_create(
                pk=feedback.id, defaults={"query_id": feedback.query_id, **values}
            )
        else:
            model, _ = FeedbackModel.objects.update_or_create(
                query_id=feedback.query_id, defaults=values
            )
        return _feedback_entity(model)
