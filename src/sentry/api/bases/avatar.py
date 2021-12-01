from PIL import Image
from rest_framework import serializers, status
from rest_framework.response import Response

from sentry.api.fields import AvatarField
from sentry.api.serializers import serialize


class AvatarSerializer(serializers.Serializer):
    avatar_photo = AvatarField(required=False)
    avatar_type = serializers.ChoiceField(
        choices=(("upload", "upload"), ("gravatar", "gravatar"), ("letter_avatar", "letter_avatar"))
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get("avatar_type") == "upload":
            model_type = self.context["type"]
            has_existing_file = model_type.objects.filter(
                file_id__isnull=False, **self.context["kwargs"]
            ).exists()
            if not has_existing_file and not attrs.get("avatar_photo"):
                raise serializers.ValidationError(
                    {"avatar_type": "Cannot set avatar_type to upload without avatar_photo"}
                )
        return attrs


class SentryAppLogoSerializer(serializers.Serializer):
    avatar_photo = AvatarField(required=False, is_sentry_app=True)
    avatar_type = serializers.ChoiceField(choices=(("default", "default"), ("upload", "upload")))
    color = serializers.BooleanField(required=True)

    def is_black_and_white(self, data):
        """Check if an image has only black or white pixels"""
        b_w = [0, 255]
        image = Image.open(data)
        w, h = image.size

        for y in range(h):
            for x in range(w):
                value = image.getpixel((y, x))
                # value is (R, G, B, A) - we don't want to check alpha
                for v in value[:-1]:
                    if v not in b_w:
                        return False
        return True

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if attrs.get("avatar_type") == "upload" and not attrs.get("avatar_photo"):
            raise serializers.ValidationError({"avatar_photo": "A logo is required."})

        if (
            not attrs.get("color")
            and attrs.get("avatar_type") == "upload"
            and not self.is_black_and_white(attrs.get("avatar_photo"))
        ):
            raise serializers.ValidationError(
                {"avatar_photo": "Issue linking icon must be black and white."}
            )

        return attrs


class AvatarMixin:
    object_type = None
    model = None

    def get(self, request, **kwargs):
        obj = kwargs.pop(self.object_type, None)
        return Response(serialize(obj, request.user, **kwargs))

    def get_serializer_context(self, obj, **kwargs):
        return {"type": self.model, "kwargs": {self.object_type: obj}}

    def get_avatar_filename(self, obj):
        return f"{obj.id}.png"

    def put(self, request, **kwargs):
        obj = kwargs.pop(self.object_type, None)

        SerializerCls = AvatarSerializer
        if self.object_type == "sentry_app":
            SerializerCls = SentryAppLogoSerializer

        serializer = SerializerCls(data=request.data, context=self.get_serializer_context(obj))

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = serializer.validated_data

        self.model.save_avatar(
            relation={self.object_type: obj},
            type=result["avatar_type"],
            avatar=result.get("avatar_photo"),
            filename=self.get_avatar_filename(obj),
            color=result.get("color"),
        )

        return Response(serialize(obj, request.user, **kwargs))
