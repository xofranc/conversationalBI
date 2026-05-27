from rest_framework.permissions import BasePermission



class IsDatasetOwner(BasePermission):
    
    '''
    Permite la accion solo si el dataset pertenece al usuario loggeado, se usa un : 
    retrieve, update y destroy
    '''
    
    
    message = 'No tienes permiso para acceder a este dataset'
    
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user