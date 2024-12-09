from ninja import Router, Form, Query, File
from ninja.pagination import paginate
from ninja.files import UploadedFile
from ninja.errors import ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.shortcuts import aget_object_or_404
from typing import List, Optional
from asgiref.sync import sync_to_async

from users.api import AsyncHttpBearer
from helpers import make_errors, image_is_valid


staff_auth = AsyncHttpBearer(is_staff=True)
router = Router(tags=['Albums'], auth=staff_auth)
