import json
from math import radians
import bpy
from mathutils import Matrix
from .template_mesh_maker import IcypTemplateMeshMaker


class ICYP_OT_MAKE_ARMATURE(bpy.types.Operator):  # noqa: N801
    bl_idname = "icyp.make_basic_armature"
    bl_label = "(WIP)basic armature"
    bl_description = "Create armature along with a simple setup for VRM export"
    bl_options = {"REGISTER", "UNDO"}

    #
    WIP_with_template_mesh: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=False
    )
    # 身長 at meter
    tall: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=1.70, min=0.3, step=0.001, name="Bone tall"  # noqa: F722
    )
    # 頭身
    head_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=8.0, min=4, step=0.05, description="height per heads"  # noqa: F722
    )
    head_width_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=2 / 3,
        min=0.3,
        max=1.2,
        step=0.05,
        description="height per heads",  # noqa: F722
    )
    # 足-胴比率:0:子供、1:大人 に近くなる(低等身で有効)
    aging_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.5, min=0, max=1, step=0.1
    )
    # 目の奥み
    eye_depth: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=-0.03, min=-0.1, max=0, step=0.005
    )
    # 肩幅
    shoulder_in_width: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.05,
        min=0.01,
        step=0.005,
        description="Inner shoulder position",  # noqa: F722
    )
    shoulder_width: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.08,
        min=0.01,
        step=0.005,
        description="shoulder roll position",  # noqa: F722
    )
    # 腕長さ率
    arm_length_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=1, min=0.5, step=0.01
    )
    # 手
    hand_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=1, min=0.5, max=2.0, step=0.05
    )
    finger_1_2_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.75,
        min=0.5,
        max=1,
        step=0.005,
        description="proximal / intermediate",  # noqa: F722,F821
    )
    finger_2_3_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.75,
        min=0.5,
        max=1,
        step=0.005,
        description="intermediate / distal",  # noqa: F722,F821
    )
    nail_bone: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=False, description="may need for finger collider"  # noqa: F722
    )  # 指先の当たり判定として必要
    # 足
    leg_length_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.5,
        min=0.3,
        max=0.6,
        step=0.01,
        description="upper body/lower body",  # noqa: F722
    )
    leg_width_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=1, min=0.01, step=0.005
    )
    leg_size: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.26, min=0.05, step=0.005
    )

    armature_obj = None

    def execute(self, context):
        self.armature_obj, compare_dict = self.make_armature(context)
        self.setup_as_vrm(self.armature_obj, compare_dict)
        if self.WIP_with_template_mesh:
            IcypTemplateMeshMaker(self)
        return {"FINISHED"}

    def head_size(self):
        return self.tall / self.head_ratio

    def hand_size(self):
        return self.head_size() * 0.75 * self.hand_ratio

    def make_armature(self, context):
        bpy.ops.object.add(type="ARMATURE", enter_editmode=True, location=(0, 0, 0))
        armature = context.object
        armature.name = "skeleton"
        armature.show_in_front = True

        bone_dic = {}

        def bone_add(name, head_pos, tail_pos, parent_bone=None, radius=0.1, roll=0):
            added_bone = armature.data.edit_bones.new(name)
            added_bone.head = head_pos
            added_bone.tail = tail_pos
            added_bone.head_radius = radius
            added_bone.tail_radius = radius
            added_bone.envelope_distance = 0.01
            added_bone.roll = radians(roll)
            if parent_bone is not None:
                added_bone.parent = parent_bone
            bone_dic.update({name: added_bone})
            return added_bone

        # bone_type = "leg" or "arm" for roll setting
        def x_mirror_bones_add(
            base_name,
            right_head_pos,
            right_tail_pos,
            parent_bones,
            radius=0.1,
            bone_type="other",
        ):
            right_roll = 0
            left_roll = 0
            if bone_type == "arm":
                right_roll = 180
            elif bone_type == "leg":
                right_roll = 90
                left_roll = 90
            left_bone = bone_add(
                base_name + "_L",
                right_head_pos,
                right_tail_pos,
                parent_bones[0],
                radius=radius,
                roll=left_roll,
            )
            right_bone = bone_add(
                base_name + "_R",
                [pos * axis for pos, axis in zip(right_head_pos, (-1, 1, 1))],
                [pos * axis for pos, axis in zip(right_tail_pos, (-1, 1, 1))],
                parent_bones[1],
                radius=radius,
                roll=right_roll,
            )

            return left_bone, right_bone

        def x_add(pos_a, add_x):
            pos = [p_a + _add for p_a, _add in zip(pos_a, [add_x, 0, 0])]
            return pos

        def y_add(pos_a, add_y):
            pos = [p_a + _add for p_a, _add in zip(pos_a, [0, add_y, 0])]
            return pos

        def z_add(pos_a, add_z):
            pos = [p_a + _add for p_a, _add in zip(pos_a, [0, 0, add_z])]
            return pos

        root = bone_add("root", (0, 0, 0), (0, 0, 0.3))
        head_size = self.head_size()
        # down side (前は8頭身の時の股上/股下の股下側割合、後ろは4頭身のときの〃を年齢具合で線形補完)(股上高めにすると破綻する)
        eight_upside_ratio, four_upside_ratio = (
            1 - self.leg_length_ratio,
            (2.5 / 4) * (1 - self.aging_ratio)
            + (1 - self.leg_length_ratio) * self.aging_ratio,
        )
        hip_up_down_ratio = (
            eight_upside_ratio * (1 - (8 - self.head_ratio) / 4)
            + four_upside_ratio * (8 - self.head_ratio) / 4
        )
        # 体幹
        # 股間
        body_separate = self.tall * (1 - hip_up_down_ratio)
        # 首の長さ
        neck_len = head_size * 2 / 3
        # 仙骨(骨盤脊柱基部)
        hips_tall = body_separate + head_size * 3 / 4
        # 胸椎・spineの全長 #首の1/3は顎の後ろに隠れてる
        backbone_len = self.tall - hips_tall - head_size - neck_len / 2
        # FIXME 胸椎と脊椎の割合の確認 //脊椎の基部に位置する主となる屈曲点と、胸郭基部に位置するもうひとつの屈曲点byHumanoid Doc
        chest_len = backbone_len * 12 / 17  # noqa: F841 mesh生成で使ってる
        spine_len = backbone_len * 5 / 17

        # 仙骨基部
        hips = bone_add("Hips", (0, 0, body_separate), (0, 0, hips_tall), root, roll=90)
        # 骨盤基部->胸郭基部
        spine = bone_add(
            "Spine", hips.tail, z_add(hips.tail, spine_len), hips, roll=-90
        )
        # 胸郭基部->首元
        chest = bone_add(
            "Chest", spine.tail, z_add(hips.tail, backbone_len), spine, roll=-90
        )
        neck = bone_add(
            "Neck",
            (0, 0, self.tall - head_size - neck_len / 2),
            (0, 0, self.tall - head_size + neck_len / 2),
            chest,
            roll=-90,
        )
        # 首の1/2は顎の後ろに隠れてる
        head = bone_add(
            "Head",
            (0, 0, self.tall - head_size + neck_len / 2),
            (0, 0, self.tall),
            neck,
            roll=-90,
        )

        # 目
        eye_depth = self.eye_depth
        eyes = x_mirror_bones_add(
            "eye",
            (head_size * self.head_width_ratio / 5, 0, self.tall - head_size / 2),
            (
                head_size * self.head_width_ratio / 5,
                eye_depth,
                self.tall - head_size / 2,
            ),
            (head, head),
        )
        # 足
        leg_width = head_size / 4 * self.leg_width_ratio
        leg_size = self.leg_size

        leg_bone_length = (body_separate + head_size * 3 / 8 - self.tall * 0.05) / 2
        upside_legs = x_mirror_bones_add(
            "Upper_Leg",
            x_add((0, 0, body_separate + head_size * 3 / 8), leg_width),
            x_add(
                z_add((0, 0, body_separate + head_size * 3 / 8), -leg_bone_length),
                leg_width,
            ),
            (hips, hips),
            radius=leg_width * 0.9,
            bone_type="leg",
        )
        lower_legs = x_mirror_bones_add(
            "Lower_Leg",
            upside_legs[0].tail,
            (leg_width, 0, self.tall * 0.05),
            upside_legs,
            radius=leg_width * 0.9,
            bone_type="leg",
        )
        foots = x_mirror_bones_add(
            "Foot",
            lower_legs[0].tail,
            (leg_width, -leg_size * (2 / 3), 0),
            lower_legs,
            radius=leg_width * 0.9,
            bone_type="leg",
        )
        toes = x_mirror_bones_add(
            "Toes",
            foots[0].tail,
            (leg_width, -leg_size, 0),
            foots,
            radius=leg_width * 0.5,
            bone_type="leg",
        )

        # 肩～指
        shoulder_in_pos = self.shoulder_in_width / 2

        shoulder_parent = chest
        shoulders = x_mirror_bones_add(
            "shoulder",
            x_add(shoulder_parent.tail, shoulder_in_pos),
            x_add(shoulder_parent.tail, shoulder_in_pos + self.shoulder_width),
            (shoulder_parent, shoulder_parent),
            radius=self.hand_size() * 0.4,
            bone_type="arm",
        )

        arm_length = (
            head_size
            * (1 * (1 - (self.head_ratio - 6) / 2) + 1.5 * ((self.head_ratio - 6) / 2))
            * self.arm_length_ratio
        )
        arms = x_mirror_bones_add(
            "Arm",
            shoulders[0].tail,
            x_add(shoulders[0].tail, arm_length),
            shoulders,
            radius=self.hand_size() * 0.4,
            bone_type="arm",
        )

        # グーにするとパーの半分くらいになる、グーのとき手を含む下腕の長さと上腕の長さが概ね一緒、けど手がでかすぎると破綻する
        forearm_length = max(arm_length - self.hand_size() / 2, arm_length * 0.8)
        forearms = x_mirror_bones_add(
            "forearm",
            arms[0].tail,
            x_add(arms[0].tail, forearm_length),
            arms,
            radius=self.hand_size() * 0.4,
            bone_type="arm",
        )
        hands = x_mirror_bones_add(
            "hand",
            forearms[0].tail,
            x_add(forearms[0].tail, self.hand_size() / 2),
            forearms,
            radius=self.hand_size() / 4,
            bone_type="arm",
        )

        def fingers(finger_name, proximal_pos, finger_len_sum):

            finger_normalize = 1 / (
                self.finger_1_2_ratio * self.finger_2_3_ratio
                + self.finger_1_2_ratio
                + 1
            )
            proximal_finger_len = finger_len_sum * finger_normalize
            intermediate_finger_len = (
                finger_len_sum * finger_normalize * self.finger_1_2_ratio
            )
            distal_finger_len = (
                finger_len_sum
                * finger_normalize
                * self.finger_1_2_ratio
                * self.finger_2_3_ratio
            )
            proximal_bones = x_mirror_bones_add(
                f"{finger_name}_proximal",
                proximal_pos,
                x_add(proximal_pos, proximal_finger_len),
                hands,
                self.hand_size() / 18,
                bone_type="arm",
            )
            intermediate_bones = x_mirror_bones_add(
                f"{finger_name}_intermediate",
                proximal_bones[0].tail,
                x_add(proximal_bones[0].tail, intermediate_finger_len),
                proximal_bones,
                self.hand_size() / 18,
                bone_type="arm",
            )
            distal_bones = x_mirror_bones_add(
                f"{finger_name}_distal",
                intermediate_bones[0].tail,
                x_add(intermediate_bones[0].tail, distal_finger_len),
                intermediate_bones,
                self.hand_size() / 18,
                bone_type="arm",
            )
            if self.nail_bone:
                x_mirror_bones_add(
                    f"{finger_name}_nail",
                    distal_bones[0].tail,
                    x_add(distal_bones[0].tail, distal_finger_len),
                    distal_bones,
                    self.hand_size() / 20,
                    bone_type="arm",
                )
            return proximal_bones, intermediate_bones, distal_bones

        finger_y_offset = -self.hand_size() / 16
        thumbs = fingers(
            "finger_thumbs",
            y_add(hands[0].head, finger_y_offset * 3),
            self.hand_size() / 2,
        )

        mats = [thumbs[0][i].matrix.translation for i in [0, 1]]
        mats = [Matrix.Translation(mat) for mat in mats]
        for j in range(3):
            for n, angle in enumerate([-45, 45]):
                thumbs[j][n].transform(mats[n].inverted())
                thumbs[j][n].transform(Matrix.Rotation(radians(angle), 4, "Z"))
                thumbs[j][n].transform(mats[n])
                thumbs[j][n].roll = [0, radians(180)][n]

        index_fingers = fingers(
            "finger_index",
            y_add(hands[0].tail, finger_y_offset * 3),
            (self.hand_size() / 2) - (1 / 2.3125) * (self.hand_size() / 2) / 3,
        )
        middle_fingers = fingers(
            "finger_middle", y_add(hands[0].tail, finger_y_offset), self.hand_size() / 2
        )
        ring_fingers = fingers(
            "finger_ring",
            y_add(hands[0].tail, -finger_y_offset),
            (self.hand_size() / 2) - (1 / 2.3125) * (self.hand_size() / 2) / 3,
        )
        little_fingers = fingers(
            "finger_little",
            y_add(hands[0].tail, -finger_y_offset * 3),
            ((self.hand_size() / 2) - (1 / 2.3125) * (self.hand_size() / 2) / 3)
            * ((1 / 2.3125) + (1 / 2.3125) * 0.75),
        )

        body_dict = {
            "hips": hips.name,
            "spine": spine.name,
            "chest": chest.name,
            "neck": neck.name,
            "head": head.name,
        }

        left_right_body_dict = {
            f"{left_right}{bone_name}": bones[lr].name
            for bone_name, bones in {
                "Eye": eyes,
                "UpperLeg": upside_legs,
                "LowerLeg": lower_legs,
                "Foot": foots,
                "Toes": toes,
                "Shoulder": shoulders,
                "UpperArm": arms,
                "LowerArm": forearms,
                "Hand": hands,
            }.items()
            for lr, left_right in enumerate(["left", "right"])
        }

        # VRM finger like name key
        fingers_dict = {
            f"{left_right}{finger_name}{position}": finger[i][lr].name
            for finger_name, finger in zip(
                ["Thumb", "Index", "Middle", "Ring", "Little"],
                [thumbs, index_fingers, middle_fingers, ring_fingers, little_fingers],
            )
            for i, position in enumerate(["Proximal", "Intermediate", "Distal"])
            for lr, left_right in enumerate(["left", "right"])
        }

        # VRM bone name : blender bone name
        bone_name_all_dict = {}
        bone_name_all_dict.update(body_dict)
        bone_name_all_dict.update(left_right_body_dict)
        bone_name_all_dict.update(fingers_dict)

        context.scene.view_layers.update()
        bpy.ops.object.mode_set(mode="OBJECT")
        context.scene.view_layers.update()
        return armature, bone_name_all_dict

    def setup_as_vrm(self, armature, compare_dict):
        for vrm_bone_name, blender_bone_name in compare_dict.items():
            armature.data[vrm_bone_name] = blender_bone_name
        ICYP_OT_MAKE_ARMATURE.make_extension_setting_and_metas(armature)

    @classmethod
    def make_extension_setting_and_metas(cls, armature):
        def write_textblock_and_assign_to_armature(block_name, value):
            text_block = bpy.data.texts.new(name=f"{armature.name}_{block_name}.json")
            text_block.write(json.dumps(value, indent=4))
            if block_name not in armature:
                armature[f"{block_name}"] = text_block.name

        # param_dicts are below of this method
        write_textblock_and_assign_to_armature(
            "humanoid_params", ICYP_OT_MAKE_ARMATURE.humanoid_params
        )
        write_textblock_and_assign_to_armature(
            "firstPerson_params", ICYP_OT_MAKE_ARMATURE.first_person_params
        )
        write_textblock_and_assign_to_armature(
            "blendshape_group", ICYP_OT_MAKE_ARMATURE.blendshape_group
        )
        write_textblock_and_assign_to_armature(
            "spring_bone", ICYP_OT_MAKE_ARMATURE.spring_bone_prams
        )

        vrm_metas = [
            "version",  # model version (not VRMspec etc)
            "author",
            "contactInformation",
            "reference",
            "title",
            "otherPermissionUrl",
            "otherLicenseUrl",
        ]
        for v in vrm_metas:
            if v not in armature:
                armature[v] = "undefined"
        required_vrm_metas = {
            "allowedUserName": "OnlyAuthor",
            "violentUssageName": "Disallow",
            "sexualUssageName": "Disallow",
            "commercialUssageName": "Disallow",
            "licenseName": "Redistribution_Prohibited",
        }
        for k, v in required_vrm_metas.items():
            if k not in armature:
                armature[k] = v

    humanoid_params = {
        "armStretch": 0.05,
        "legStretch": 0.05,
        "upperArmTwist": 0.5,
        "lowerArmTwist": 0.5,
        "upperLegTwist": 0.5,
        "lowerLegTwist": 0.5,
        "feetSpacing": 0,
        "hasTranslationDoF": False,
    }
    first_person_params = {
        "firstPersonBone": "Head",
        "firstPersonBoneOffset": {"x": 0, "y": 0, "z": 0},
        "meshAnnotations": [],
        "lookAtTypeName": "Bone",
        "lookAtHorizontalInner": {
            "curve": [0, 0, 0, 1, 1, 1, 1, 0],
            "xRange": 90,
            "yRange": 8,
        },
        "lookAtHorizontalOuter": {
            "curve": [0, 0, 0, 1, 1, 1, 1, 0],
            "xRange": 90,
            "yRange": 12,
        },
        "lookAtVerticalDown": {
            "curve": [0, 0, 0, 1, 1, 1, 1, 0],
            "xRange": 90,
            "yRange": 10,
        },
        "lookAtVerticalUp": {
            "curve": [0, 0, 0, 1, 1, 1, 1, 0],
            "xRange": 90,
            "yRange": 10,
        },
    }

    blendshape_group = [
        {
            "name": "Neutral",
            "presetName": "neutral",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "A",
            "presetName": "a",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "I",
            "presetName": "i",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "U",
            "presetName": "u",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "E",
            "presetName": "e",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "O",
            "presetName": "o",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "Blink",
            "presetName": "blink",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "Joy",
            "presetName": "joy",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "Angry",
            "presetName": "angry",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "Sorrow",
            "presetName": "sorrow",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "Fun",
            "presetName": "fun",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "LookUp",
            "presetName": "lookup",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "LookDown",
            "presetName": "lookdown",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "LookLeft",
            "presetName": "lookleft",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "LookRight",
            "presetName": "lookright",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "Blink_L",
            "presetName": "blink_l",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
        {
            "name": "Blink_R",
            "presetName": "blink_r",
            "binds": [],
            "materialValues": [],
            "isBinary": False,
        },
    ]

    spring_bone_prams = [
        {
            "comment": "",
            "stiffiness": 1,
            "gravityPower": 0,
            "gravityDir": {"x": 0, "y": -1, "z": 0},
            "dragForce": 0.4,
            "center": -1,
            "hitRadius": 0.02,
            "bones": [],
            "colliderGroups": [],
        }
    ]
