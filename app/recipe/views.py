from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Tag, Ingredient, Recipe
from recipe import serializers
from recipe.serializers import TagSerializer, IngredientSerializer, RecipeSerializer


class BaseRecipeAttrViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(BaseRecipeAttrViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # noinspection PyMethodMayBeStatic
    def _params_to_ints(self, id_list):
        return [int(str_id) for str_id in id_list.split(',')]

    def get_queryset(self):
        queryset = self.queryset
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')

        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__in=tag_ids)

        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__in=ingredient_ids)

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return serializers.RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer: RecipeSerializer = self.get_serializer(
            recipe,
            data=self.request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
