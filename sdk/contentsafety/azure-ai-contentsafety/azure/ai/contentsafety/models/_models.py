# coding=utf-8
# pylint: disable=too-many-lines
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) Python Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

from typing import Any, List, Mapping, Optional, TYPE_CHECKING, Union, overload

from .. import _model_base
from .._model_base import rest_field

if TYPE_CHECKING:
    # pylint: disable=unused-import,ungrouped-imports
    from .. import models as _models


class AddBlockItemsOptions(_model_base.Model):
    """The request of adding blockItems to text blocklist.

    All required parameters must be populated in order to send to Azure.

    :ivar block_items: Array of blockItemInfo to add. Required.
    :vartype block_items: list[~azure.ai.contentsafety.models.TextBlockItemInfo]
    """

    block_items: List["_models.TextBlockItemInfo"] = rest_field(name="blockItems")
    """Array of blockItemInfo to add. Required."""

    @overload
    def __init__(
        self,
        *,
        block_items: List["_models.TextBlockItemInfo"],
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class AddBlockItemsResult(_model_base.Model):
    """The response of adding blockItems to text blocklist.

    :ivar value: Array of blockItems added.
    :vartype value: list[~azure.ai.contentsafety.models.TextBlockItem]
    """

    value: Optional[List["_models.TextBlockItem"]] = rest_field()
    """Array of blockItems added."""

    @overload
    def __init__(
        self,
        *,
        value: Optional[List["_models.TextBlockItem"]] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class AnalyzeImageOptions(_model_base.Model):
    """The analysis request of the image.

    All required parameters must be populated in order to send to Azure.

    :ivar image: The image needs to be analyzed. Required.
    :vartype image: ~azure.ai.contentsafety.models.ImageData
    :ivar categories: The categories will be analyzed. If not assigned, a default set of the
     categories' analysis results will be returned.
    :vartype categories: list[str or ~azure.ai.contentsafety.models.ImageCategory]
    """

    image: "_models.ImageData" = rest_field()
    """The image needs to be analyzed. Required."""
    categories: Optional[List[Union[str, "_models.ImageCategory"]]] = rest_field()
    """The categories will be analyzed. If not assigned, a default set of the categories' analysis
     results will be returned."""

    @overload
    def __init__(
        self,
        *,
        image: "_models.ImageData",
        categories: Optional[List[Union[str, "_models.ImageCategory"]]] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class AnalyzeImageResult(_model_base.Model):
    """The analysis response of the image.

    :ivar hate_result: Analysis result for Hate category.
    :vartype hate_result: ~azure.ai.contentsafety.models.ImageAnalyzeSeverityResult
    :ivar self_harm_result: Analysis result for SelfHarm category.
    :vartype self_harm_result: ~azure.ai.contentsafety.models.ImageAnalyzeSeverityResult
    :ivar sexual_result: Analysis result for Sexual category.
    :vartype sexual_result: ~azure.ai.contentsafety.models.ImageAnalyzeSeverityResult
    :ivar violence_result: Analysis result for Violence category.
    :vartype violence_result: ~azure.ai.contentsafety.models.ImageAnalyzeSeverityResult
    """

    hate_result: Optional["_models.ImageAnalyzeSeverityResult"] = rest_field(name="hateResult")
    """Analysis result for Hate category."""
    self_harm_result: Optional["_models.ImageAnalyzeSeverityResult"] = rest_field(name="selfHarmResult")
    """Analysis result for SelfHarm category."""
    sexual_result: Optional["_models.ImageAnalyzeSeverityResult"] = rest_field(name="sexualResult")
    """Analysis result for Sexual category."""
    violence_result: Optional["_models.ImageAnalyzeSeverityResult"] = rest_field(name="violenceResult")
    """Analysis result for Violence category."""

    @overload
    def __init__(
        self,
        *,
        hate_result: Optional["_models.ImageAnalyzeSeverityResult"] = None,
        self_harm_result: Optional["_models.ImageAnalyzeSeverityResult"] = None,
        sexual_result: Optional["_models.ImageAnalyzeSeverityResult"] = None,
        violence_result: Optional["_models.ImageAnalyzeSeverityResult"] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class AnalyzeTextOptions(_model_base.Model):
    """The analysis request of the text.

    All required parameters must be populated in order to send to Azure.

    :ivar text: The text needs to be scanned. We support at most 1000 characters (unicode code
     points) in text of one request. Required.
    :vartype text: str
    :ivar categories: The categories will be analyzed. If not assigned, a default set of the
     categories' analysis results will be returned.
    :vartype categories: list[str or ~azure.ai.contentsafety.models.TextCategory]
    :ivar blocklist_names: The names of blocklists.
    :vartype blocklist_names: list[str]
    :ivar break_by_blocklists: When set to true, further analyses of harmful content will not be
     performed in cases where blocklists are hit. When set to false, all analyses of harmful content
     will be performed, whether or not blocklists are hit.
    :vartype break_by_blocklists: bool
    """

    text: str = rest_field()
    """The text needs to be scanned. We support at most 1000 characters (unicode code points) in text
     of one request. Required."""
    categories: Optional[List[Union[str, "_models.TextCategory"]]] = rest_field()
    """The categories will be analyzed. If not assigned, a default set of the categories' analysis
     results will be returned."""
    blocklist_names: Optional[List[str]] = rest_field(name="blocklistNames")
    """The names of blocklists."""
    break_by_blocklists: Optional[bool] = rest_field(name="breakByBlocklists")
    """When set to true, further analyses of harmful content will not be performed in cases where
     blocklists are hit. When set to false, all analyses of harmful content will be performed,
     whether or not blocklists are hit."""

    @overload
    def __init__(
        self,
        *,
        text: str,
        categories: Optional[List[Union[str, "_models.TextCategory"]]] = None,
        blocklist_names: Optional[List[str]] = None,
        break_by_blocklists: Optional[bool] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class AnalyzeTextResult(_model_base.Model):
    """The analysis response of the text.

    :ivar blocklists_match_results: The details of blocklist match.
    :vartype blocklists_match_results:
     list[~azure.ai.contentsafety.models.TextBlocklistMatchResult]
    :ivar hate_result: Analysis result for Hate category.
    :vartype hate_result: ~azure.ai.contentsafety.models.TextAnalyzeSeverityResult
    :ivar self_harm_result: Analysis result for SelfHarm category.
    :vartype self_harm_result: ~azure.ai.contentsafety.models.TextAnalyzeSeverityResult
    :ivar sexual_result: Analysis result for Sexual category.
    :vartype sexual_result: ~azure.ai.contentsafety.models.TextAnalyzeSeverityResult
    :ivar violence_result: Analysis result for Violence category.
    :vartype violence_result: ~azure.ai.contentsafety.models.TextAnalyzeSeverityResult
    """

    blocklists_match_results: Optional[List["_models.TextBlocklistMatchResult"]] = rest_field(
        name="blocklistsMatchResults"
    )
    """The details of blocklist match."""
    hate_result: Optional["_models.TextAnalyzeSeverityResult"] = rest_field(name="hateResult")
    """Analysis result for Hate category."""
    self_harm_result: Optional["_models.TextAnalyzeSeverityResult"] = rest_field(name="selfHarmResult")
    """Analysis result for SelfHarm category."""
    sexual_result: Optional["_models.TextAnalyzeSeverityResult"] = rest_field(name="sexualResult")
    """Analysis result for Sexual category."""
    violence_result: Optional["_models.TextAnalyzeSeverityResult"] = rest_field(name="violenceResult")
    """Analysis result for Violence category."""

    @overload
    def __init__(
        self,
        *,
        blocklists_match_results: Optional[List["_models.TextBlocklistMatchResult"]] = None,
        hate_result: Optional["_models.TextAnalyzeSeverityResult"] = None,
        self_harm_result: Optional["_models.TextAnalyzeSeverityResult"] = None,
        sexual_result: Optional["_models.TextAnalyzeSeverityResult"] = None,
        violence_result: Optional["_models.TextAnalyzeSeverityResult"] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class ImageAnalyzeSeverityResult(_model_base.Model):
    """Image analysis result.

    All required parameters must be populated in order to send to Azure.

    :ivar category: The image category. Required. Known values are: "Hate", "SelfHarm", "Sexual",
     and "Violence".
    :vartype category: str or ~azure.ai.contentsafety.models.ImageCategory
    :ivar severity: The higher the severity of input content, the larger this value, currently its
     value could be: 0,2,4,6. Required.
    :vartype severity: int
    """

    category: Union[str, "_models.ImageCategory"] = rest_field()
    """The image category. Required. Known values are: \"Hate\", \"SelfHarm\", \"Sexual\", and
     \"Violence\"."""
    severity: int = rest_field()
    """The higher the severity of input content, the larger this value, currently its value could be:
     0,2,4,6. Required."""

    @overload
    def __init__(
        self,
        *,
        category: Union[str, "_models.ImageCategory"],
        severity: int,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class ImageData(_model_base.Model):
    """The content or blob url of image, could be base64 encoding bytes or blob url. If both are
    given, the request will be refused. The maximum size of image is 2048 pixels * 2048 pixels, no
    larger than 4MB at the same time. The minimum size of image is 50 pixels * 50 pixels.

    :ivar content: Base64 encoding of image.
    :vartype content: bytes
    :ivar blob_url: The blob url of image.
    :vartype blob_url: str
    """

    content: Optional[bytes] = rest_field()
    """Base64 encoding of image."""
    blob_url: Optional[str] = rest_field(name="blobUrl")
    """The blob url of image."""

    @overload
    def __init__(
        self,
        *,
        content: Optional[bytes] = None,
        blob_url: Optional[str] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class RemoveBlockItemsOptions(_model_base.Model):
    """The request of removing blockItems from text blocklist.

    All required parameters must be populated in order to send to Azure.

    :ivar block_item_ids: Array of blockItemIds to remove. Required.
    :vartype block_item_ids: list[str]
    """

    block_item_ids: List[str] = rest_field(name="blockItemIds")
    """Array of blockItemIds to remove. Required."""

    @overload
    def __init__(
        self,
        *,
        block_item_ids: List[str],
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class TextAnalyzeSeverityResult(_model_base.Model):
    """Text analysis result.

    All required parameters must be populated in order to send to Azure.

    :ivar category: The text category. Required. Known values are: "Hate", "SelfHarm", "Sexual",
     and "Violence".
    :vartype category: str or ~azure.ai.contentsafety.models.TextCategory
    :ivar severity: The higher the severity of input content, the larger this value is. The values
     could be: 0,2,4,6. Required.
    :vartype severity: int
    """

    category: Union[str, "_models.TextCategory"] = rest_field()
    """The text category. Required. Known values are: \"Hate\", \"SelfHarm\", \"Sexual\", and
     \"Violence\"."""
    severity: int = rest_field()
    """The higher the severity of input content, the larger this value is. The values could be:
     0,2,4,6. Required."""

    @overload
    def __init__(
        self,
        *,
        category: Union[str, "_models.TextCategory"],
        severity: int,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class TextBlockItem(_model_base.Model):
    """Item in TextBlocklist.

    All required parameters must be populated in order to send to Azure.

    :ivar block_item_id: Block Item Id. It will be uuid. Required.
    :vartype block_item_id: str
    :ivar description: Block item description.
    :vartype description: str
    :ivar text: Block item content. Required.
    :vartype text: str
    """

    block_item_id: str = rest_field(name="blockItemId")
    """Block Item Id. It will be uuid. Required."""
    description: Optional[str] = rest_field()
    """Block item description."""
    text: str = rest_field()
    """Block item content. Required."""

    @overload
    def __init__(
        self,
        *,
        block_item_id: str,
        text: str,
        description: Optional[str] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class TextBlockItemInfo(_model_base.Model):
    """Block item info in text blocklist.

    All required parameters must be populated in order to send to Azure.

    :ivar description: Block item description.
    :vartype description: str
    :ivar text: Block item content. Required.
    :vartype text: str
    """

    description: Optional[str] = rest_field()
    """Block item description."""
    text: str = rest_field()
    """Block item content. Required."""

    @overload
    def __init__(
        self,
        *,
        text: str,
        description: Optional[str] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class TextBlocklist(_model_base.Model):
    """Text Blocklist.

    All required parameters must be populated in order to send to Azure.

    :ivar blocklist_name: Text blocklist name. Required.
    :vartype blocklist_name: str
    :ivar description: Text blocklist description.
    :vartype description: str
    """

    blocklist_name: str = rest_field(name="blocklistName")
    """Text blocklist name. Required."""
    description: Optional[str] = rest_field()
    """Text blocklist description."""

    @overload
    def __init__(
        self,
        *,
        blocklist_name: str,
        description: Optional[str] = None,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)


class TextBlocklistMatchResult(_model_base.Model):
    """The result of blocklist match.

    All required parameters must be populated in order to send to Azure.

    :ivar blocklist_name: The name of matched blocklist. Required.
    :vartype blocklist_name: str
    :ivar block_item_id: The id of matched item. Required.
    :vartype block_item_id: str
    :ivar block_item_text: The content of matched item. Required.
    :vartype block_item_text: str
    :ivar offset: The character offset of matched text in original input. Required.
    :vartype offset: int
    :ivar length: The length of matched text in original input. Required.
    :vartype length: int
    """

    blocklist_name: str = rest_field(name="blocklistName")
    """The name of matched blocklist. Required."""
    block_item_id: str = rest_field(name="blockItemId")
    """The id of matched item. Required."""
    block_item_text: str = rest_field(name="blockItemText")
    """The content of matched item. Required."""
    offset: int = rest_field()
    """The character offset of matched text in original input. Required."""
    length: int = rest_field()
    """The length of matched text in original input. Required."""

    @overload
    def __init__(
        self,
        *,
        blocklist_name: str,
        block_item_id: str,
        block_item_text: str,
        offset: int,
        length: int,
    ):
        ...

    @overload
    def __init__(self, mapping: Mapping[str, Any]):
        """
        :param mapping: raw JSON to initialize the model.
        :type mapping: Mapping[str, Any]
        """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(*args, **kwargs)