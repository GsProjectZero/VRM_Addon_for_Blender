"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import math
import struct
from sys import float_info
from typing import Any, Dict, List, Optional, Sequence, Union, cast

import bpy


class Gltf:
    TEXTURE_INPUT_NAMES = [
        "color_texture",
        "normal",
        "emissive_texture",
        "occlusion_texture",
    ]
    VAL_INPUT_NAMES = ["metallic", "roughness", "unlit"]
    RGBA_INPUT_NAMES = ["base_Color", "emissive_color"]


class Vrm0:
    METAS = [
        "version",  # model version (not VRMspec etc)
        "author",
        "contactInformation",
        "reference",
        "title",
        "otherPermissionUrl",
        "otherLicenseUrl",
    ]
    REQUIRED_METAS = {
        "allowedUserName": "OnlyAuthor",
        "violentUssageName": "Disallow",
        "sexualUssageName": "Disallow",
        "commercialUssageName": "Disallow",
        "licenseName": "Redistribution_Prohibited",
    }
    HUMANOID_DEFAULT_PARAMS: Dict[str, Union[float, bool]] = {
        "armStretch": 0.05,
        "legStretch": 0.05,
        "upperArmTwist": 0.5,
        "lowerArmTwist": 0.5,
        "upperLegTwist": 0.5,
        "lowerLegTwist": 0.5,
        "feetSpacing": 0,
        "hasTranslationDoF": False,
    }
    FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS = {
        "curve": [0, 0, 0, 1, 1, 1, 1, 0],
        "xRange": 90,
        "yRange": 10,
    }
    FIRST_PERSON_DEFAULT_PARAMS: Dict[str, Any] = {
        "firstPersonBone": -1,
        "firstPersonBoneOffset": {"x": 0, "y": 0.06, "z": 0},
        "lookAtHorizontalInner": FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS,
        "lookAtHorizontalOuter": FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS,
        "lookAtTypeName": "Bone",
        "lookAtVerticalDown": FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS,
        "lookAtVerticalUp": FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS,
        "meshAnnotations": [],
    }


class Vrm1:
    METAS: List[str] = []
    REQUIRED_METAS: Dict[str, str] = {}


class VrmPydata:
    def __init__(self, filepath: str, json: Dict[str, Any]) -> None:
        self.filepath = filepath
        self.json = json
        self.decoded_binary: List[Any] = []
        self.image_properties: List[ImageProps] = []
        self.meshes: List[List[Mesh]] = []
        self.materials: List[Material] = []
        self.nodes_dict: Dict[int, Node] = {}
        self.origin_nodes_dict: Dict[int, List[Any]] = {}
        self.skins_joints_list: List[List[int]] = []
        self.skins_root_node_list: List[int] = []


class Mesh:
    def __init__(self, object_id: int) -> None:
        self.name = ""
        self.face_indices: Any = []  # ndarray
        self.skin_id: Optional[int] = None
        self.object_id = object_id
        self.material_index: Optional[int] = None
        self.POSITION_accessor: Optional[int] = None
        self.POSITION: Optional[List[List[float]]] = None
        self.JOINTS_0: Optional[List[List[int]]] = None
        self.WEIGHTS_0: Optional[List[List[float]]] = None
        self.NORMAL: Optional[List[List[float]]] = None
        self.vert_normal_normalized: Optional[bool] = None
        self.morph_target_point_list_and_accessor_index_dict: Optional[
            Dict[str, List[Any]]
        ] = None


class Node:
    def __init__(
        self,
        name: str,
        position: Sequence[float],
        rotation: Sequence[float],
        scale: Sequence[float],
    ) -> None:
        self.name = name
        self.position = position
        self.rotation = rotation
        self.scale = scale
        self.children: Optional[List[int]] = None
        self.blend_bone: Optional[bpy.types.Bone] = None
        self.mesh_id: Optional[int] = None
        self.skin_id: Optional[int] = None


class HumanBones:
    center_req = ["hips", "spine", "chest", "neck", "head"]
    left_leg_req = ["leftUpperLeg", "leftLowerLeg", "leftFoot"]
    left_arm_req = ["leftUpperArm", "leftLowerArm", "leftHand"]
    right_leg_req = ["rightUpperLeg", "rightLowerLeg", "rightFoot"]
    right_arm_req = ["rightUpperArm", "rightLowerArm", "rightHand"]

    requires = [
        *center_req[:],
        *left_leg_req[:],
        *right_leg_req[:],
        *left_arm_req[:],
        *right_arm_req[:],
    ]

    left_arm_def = [
        "leftShoulder",
        "leftThumbProximal",
        "leftThumbIntermediate",
        "leftThumbDistal",
        "leftIndexProximal",
        "leftIndexIntermediate",
        "leftIndexDistal",
        "leftMiddleProximal",
        "leftMiddleIntermediate",
        "leftMiddleDistal",
        "leftRingProximal",
        "leftRingIntermediate",
        "leftRingDistal",
        "leftLittleProximal",
        "leftLittleIntermediate",
        "leftLittleDistal",
    ]

    right_arm_def = [
        "rightShoulder",
        "rightThumbProximal",
        "rightThumbIntermediate",
        "rightThumbDistal",
        "rightIndexProximal",
        "rightIndexIntermediate",
        "rightIndexDistal",
        "rightMiddleProximal",
        "rightMiddleIntermediate",
        "rightMiddleDistal",
        "rightRingProximal",
        "rightRingIntermediate",
        "rightRingDistal",
        "rightLittleProximal",
        "rightLittleIntermediate",
        "rightLittleDistal",
    ]
    center_def = ["upperChest", "jaw"]
    left_leg_def = ["leftToes"]
    right_leg_def = ["rightToes"]
    defines = [
        "leftEye",
        "rightEye",
        *center_def[:],
        *left_leg_def[:],
        *right_leg_def[:],
        *left_arm_def[:],
        *right_arm_def[:],
    ]
    # child:parent
    hierarchy: Dict[str, str] = {
        # 体幹
        "leftEye": "head",
        "rightEye": "head",
        "jaw": "head",
        "head": "neck",
        "neck": "upperChest",
        "upperChest": "chest",
        "chest": "spine",
        "spine": "hips",  # root
        # 右上
        "rightShoulder": "chest",
        "rightUpperArm": "rightShoulder",
        "rightLowerArm": "rightUpperArm",
        "rightHand": "rightLowerArm",
        "rightThumbProximal": "rightHand",
        "rightThumbIntermediate": "rightThumbProximal",
        "rightThumbDistal": "rightThumbIntermediate",
        "rightIndexProximal": "rightHand",
        "rightIndexIntermediate": "rightIndexProximal",
        "rightIndexDistal": "rightIndexIntermediate",
        "rightMiddleProximal": "rightHand",
        "rightMiddleIntermediate": "rightMiddleProximal",
        "rightMiddleDistal": "rightMiddleIntermediate",
        "rightRingProximal": "rightHand",
        "rightRingIntermediate": "rightRingProximal",
        "rightRingDistal": "rightRingIntermediate",
        "rightLittleProximal": "rightHand",
        "rightLittleIntermediate": "rightLittleProximal",
        "rightLittleDistal": "rightLittleIntermediate",
        # 左上
        "leftShoulder": "chest",
        "leftUpperArm": "leftShoulder",
        "leftLowerArm": "leftUpperArm",
        "leftHand": "leftLowerArm",
        "leftThumbProximal": "leftHand",
        "leftThumbIntermediate": "leftThumbProximal",
        "leftThumbDistal": "leftThumbIntermediate",
        "leftIndexProximal": "leftHand",
        "leftIndexIntermediate": "leftIndexProximal",
        "leftIndexDistal": "leftIndexIntermediate",
        "leftMiddleProximal": "leftHand",
        "leftMiddleIntermediate": "leftMiddleProximal",
        "leftMiddleDistal": "leftMiddleIntermediate",
        "leftRingProximal": "leftHand",
        "leftRingIntermediate": "leftRingProximal",
        "leftRingDistal": "leftRingIntermediate",
        "leftLittleProximal": "leftHand",
        "leftLittleIntermediate": "leftLittleProximal",
        "leftLittleDistal": "leftLittleIntermediate",
        # 左足
        "leftUpperLeg": "hips",
        "leftLowerLeg": "leftUpperLeg",
        "leftFoot": "leftLowerLeg",
        "leftToes": "leftFoot",
        # 右足
        "rightUpperLeg": "hips",
        "rightLowerLeg": "rightUpperLeg",
        "rightFoot": "rightLowerLeg",
        "rightToes": "rightFoot",
    }


class ImageProps:
    def __init__(self, name: str, filepath: str, filetype: str) -> None:
        self.name = name
        self.filepath = filepath
        self.filetype = filetype


class Material:
    def __init__(self) -> None:
        self.name = ""
        self.shader_name = ""


class MaterialGltf(Material):
    def __init__(self) -> None:
        super().__init__()

        self.base_color: List[float] = [1, 1, 1, 1]
        self.metallic_factor: float = 1
        self.roughness_factor: float = 1
        self.emissive_factor: List[float] = [0, 0, 0]

        self.color_texture_index: Optional[int] = None
        self.color_texcoord_index: Optional[int] = None
        self.metallic_roughness_texture_index: Optional[int] = None
        self.metallic_roughness_texture_texcoord: Optional[int] = None
        self.normal_texture_index: Optional[int] = None
        self.normal_texture_texcoord_index: Optional[int] = None
        self.emissive_texture_index: Optional[int] = None
        self.emissive_texture_texcoord_index: Optional[int] = None
        self.occlusion_texture_index: Optional[int] = None
        self.occlusion_texture_texcoord_index: Optional[int] = None
        self.alphaCutoff: Optional[float] = None

        self.double_sided = False
        self.alpha_mode = "OPAQUE"
        self.shadeless = 0  # 0 is shade ,1 is shadeless

        self.vrm_addon_for_blender_legacy_gltf_material = False


class MaterialTransparentZWrite(Material):
    float_props = [
        "_MainTex",
        "_Cutoff",
        "_BlendMode",
        "_CullMode",
        "_VColBlendMode",
        "_SrcBlend",
        "_DstBlend",
        "_ZWrite",
    ]
    texture_index_list = ["_MainTex"]
    vector_props = ["_Color"]

    def __init__(self) -> None:
        super().__init__()
        self.float_props_dic: Dict[str, Optional[float]] = {
            prop: None for prop in self.float_props
        }
        self.vector_props_dic: Dict[str, Optional[List[float]]] = {
            prop: None for prop in self.vector_props
        }
        self.texture_index_dic: Dict[str, Optional[int]] = {
            tex: None for tex in self.texture_index_list
        }


class MaterialMtoon(Material):
    # {key = MToonProp, val = ShaderNodeGroup_member_name}
    version = 32
    float_props_exchange_dic: Dict[str, Optional[str]] = {
        "_MToonVersion": None,
        "_Cutoff": "CutoffRate",
        "_BumpScale": "BumpScale",
        "_ReceiveShadowRate": "ReceiveShadowRate",
        "_ShadeShift": "ShadeShift",
        "_ShadeToony": "ShadeToony",
        "_RimLightingMix": "RimLightingMix",
        "_RimFresnelPower": "RimFresnelPower",
        "_RimLift": "RimLift",
        "_ShadingGradeRate": "ShadingGradeRate",
        "_LightColorAttenuation": "LightColorAttenuation",
        "_IndirectLightIntensity": "IndirectLightIntensity",
        "_OutlineWidth": "OutlineWidth",
        "_OutlineScaledMaxDistance": "OutlineScaleMaxDistance",
        "_OutlineLightingMix": "OutlineLightingMix",
        "_UvAnimScrollX": "UV_Scroll_X",  # TODO #####
        "_UvAnimScrollY": "UV_Scroll_Y",  # TODO #####
        "_UvAnimRotation": "UV_Scroll_Rotation",  # TODO #####
        "_DebugMode": None,
        "_BlendMode": None,
        "_OutlineWidthMode": "OutlineWidthMode",
        "_OutlineColorMode": "OutlineColorMode",
        "_CullMode": None,
        "_OutlineCullMode": None,
        "_SrcBlend": None,
        "_DstBlend": None,
        "_ZWrite": None,
        "_IsFirstSetup": None,
    }

    texture_kind_exchange_dic: Dict[str, str] = {
        "_MainTex": "MainTexture",
        "_ShadeTexture": "ShadeTexture",
        "_BumpMap": "NormalmapTexture",
        "_ReceiveShadowTexture": "ReceiveShadow_Texture",
        "_ShadingGradeTexture": "ShadingGradeTexture",
        "_EmissionMap": "Emission_Texture",
        "_SphereAdd": "SphereAddTexture",
        "_RimTexture": "RimTexture",
        "_OutlineWidthTexture": "OutlineWidthTexture",
        "_UvAnimMaskTexture": "UV_Animation_Mask_Texture",  # TODO ####
    }
    vector_base_props_exchange_dic: Dict[str, str] = {
        "_Color": "DiffuseColor",
        "_ShadeColor": "ShadeColor",
        "_EmissionColor": "EmissionColor",
        "_RimColor": "RimColor",
        "_OutlineColor": "OutlineColor",
    }
    # texture offset and scaling props by texture
    vector_props_exchange_dic = {}
    vector_props_exchange_dic.update(vector_base_props_exchange_dic)
    vector_props_exchange_dic.update(texture_kind_exchange_dic)

    keyword_list = [
        "_NORMALMAP",
        "_ALPHATEST_ON",
        "_ALPHABLEND_ON",
        "_ALPHAPREMULTIPLY_ON",
        "MTOON_OUTLINE_WIDTH_WORLD",
        "MTOON_OUTLINE_WIDTH_SCREEN",
        "MTOON_OUTLINE_COLOR_FIXED",
        "MTOON_OUTLINE_COLOR_MIXED",
        "MTOON_DEBUG_NORMAL",
        "MTOON_DEBUG_LITSHADERATE",
    ]
    tagmap_list = ["RenderType"]

    def __init__(self) -> None:
        super().__init__()
        self.float_props_dic: Dict[str, Optional[float]] = {
            prop: None for prop in self.float_props_exchange_dic
        }
        self.vector_props_dic: Dict[str, Optional[Sequence[float]]] = {
            prop: None for prop in self.vector_props_exchange_dic
        }
        self.texture_index_dic: Dict[str, Optional[int]] = {
            prop: None for prop in self.texture_kind_exchange_dic
        }
        self.keyword_dic: Dict[str, bool] = {kw: False for kw in self.keyword_list}
        self.tag_dic: Dict[str, Optional[str]] = {tag: None for tag in self.tagmap_list}


def make_json_return_value(
    v: Any,
) -> Union[int, bool, float, str, List[Any], Dict[str, Any], None]:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return v

    print(f"WARNING: {v} is unrecognized type")
    return cast(Optional[Union[int, bool, float, str, List[Any], Dict[str, Any]]], v)


def nested_json_value_getter(
    json: Optional[Union[Dict[str, Any], List[Any]]],
    attrs: List[Union[int, str]],
    default: Optional[Union[int, float, str, List[Any], Dict[str, Any]]] = None,
) -> Union[int, bool, float, str, List[Any], Dict[str, Any], None]:
    if json is None:
        return default

    attr = attrs.pop(0)

    if isinstance(json, list) and isinstance(attr, int) and 0 <= attr < len(json):
        if not attrs:
            return make_json_return_value(json[attr])
        return nested_json_value_getter(json[attr], attrs, default)

    if isinstance(json, dict) and isinstance(attr, str) and attr in json:
        if not attrs:
            return make_json_return_value(json[attr])
        return nested_json_value_getter(json[attr], attrs, default)

    return default


def nested_json_list_getter(
    json: Optional[Union[Dict[str, Any], List[Any]]],
    attrs: List[Union[int, str]],
    default: List[Any],
) -> List[Any]:
    result = nested_json_value_getter(json, attrs, default)
    return result if isinstance(result, list) else default


def normalize_weights_compatible_with_gl_float(
    weights: Sequence[float],
) -> Sequence[float]:
    if abs(sum(weights) - 1.0) < float_info.epsilon:
        return weights

    def to_gl_float(array4: Sequence[float]) -> Sequence[float]:
        return list(struct.unpack("<ffff", struct.pack("<ffff", *array4)))

    # Simulate export and import
    weights = to_gl_float(weights)
    for _ in range(10):
        next_weights = to_gl_float([weights[i] / sum(weights) for i in range(4)])
        error = abs(1 - math.fsum(weights))
        next_error = abs(1 - math.fsum(next_weights))
        if error >= float_info.epsilon and error > next_error:
            weights = next_weights
        else:
            break

    return weights


if __name__ == "__main__":
    pass
