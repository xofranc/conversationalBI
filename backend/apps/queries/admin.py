from django.contrib import admin
from .models.queryFeedback import QueryFeedback
from .models.queryHistory import QueryHistory
from .models.queryResult import QueryResult

@admin.register(QueryFeedback)
class QueryFeedbackAdmin(admin.ModelAdmin):
    list_display = ('query_id', 'score', 'created_at')
    list_filter = ('score',)

@admin.register(QueryHistory)
class QueryHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'success', 'model_used', 'created_at')
    list_filter = ('success', 'model_used', 'cached')
    search_fields = ('question', 'sql_generated')

@admin.register(QueryResult)
class QueryResultAdmin(admin.ModelAdmin):
    list_display = ('query_id', 'row_count', 'chart_type')