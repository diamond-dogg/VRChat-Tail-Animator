#!/usr/bin/env python3
import math
def main():

    # --------------------------------------------------------------------------------
    # 1) PARAMETERS  
    # --------------------------------------------------------------------------------

    # Output file path
    output_path = r"TailSway.anim"

    # Overall timing / sway
    num_keyframes = 60                 # total number of keyframes (recommend at least 30)
    length_of_loop = 5.5               # total animation length in seconds (also controls speed of the wag of course)
    sway_amount = 17.0                 # amplitude of the tail sway in degrees
    follow_through_delay = 0.062       # fraction of total time with which each subsequent bone lags behind the last (adds follow-through to the animation). Less follow through for a dog-like wag, more follow through for a feline sway.


    # Base angle of the root of the tail (in degrees)
    root_angle = 18.0

    # Per-bone incremental curl: each subsequent bone in the chain adds this many degrees (multiplied by the bone index^exponent)  -  pow(float(i), bone_curl_A_exponent) * bone_curl_A
    bone_curl_A_exponent = 0.75
    bone_curl_A = -14.5

    # Secondary incremental curl. Can be used with a higher power to add extra curl to the tip. Also, animates between min and max as tail wags (to allow for slight uncurling as the tail hits the peaks of each wag)
    bone_curl_B_exponent = 1.1
    bone_curl_B_min = 9.0
    bone_curl_B_max = 13.0


    # Bone paths (make sure this aligns with your actual bone hierarchy). Should typically start with Armature, do not start with your avatar prefab name itself.
    tail_bones = [
        "Armature/Hips/tailroot",
        "Armature/Hips/tailroot/tail1",
        "Armature/Hips/tailroot/tail1/tail2",
        "Armature/Hips/tailroot/tail1/tail2/tail3",
        "Armature/Hips/tailroot/tail1/tail2/tail3/tail4",
        "Armature/Hips/tailroot/tail1/tail2/tail3/tail4/tail5",
        "Armature/Hips/tailroot/tail1/tail2/tail3/tail4/tail5/tail6",
        "Armature/Hips/tailroot/tail1/tail2/tail3/tail4/tail5/tail6/tail7",
        "Armature/Hips/tailroot/tail1/tail2/tail3/tail4/tail5/tail6/tail7/tail8",
    ]











    # --------------------------------------------------------------------------------
    # 2) GENERATE ROTATION DATA
    # --------------------------------------------------------------------------------

    #   - m_EulerCurves (as a single vector curve)
    #   - m_EditorCurves (broken out into x/y/z for the editor)
    times = [ (length_of_loop * i / (num_keyframes - 1)) for i in range(num_keyframes) ]
    omega = 2.0 * math.pi / length_of_loop

    # Data structures:
    # euler_keyframes[bone] = [(time, (x_val, y_val, z_val)), ...]
    # editor_curves[bone]['x'] = [(time, val), ...], etc.
    euler_keyframes = {}
    editor_curves = {}
    for b in tail_bones:
        euler_keyframes[b] = []
        editor_curves[b] = { 'x': [], 'y': [], 'z': [] }

    for i, bone in enumerate(tail_bones):
        # Offset in time
        follow_through_secs = follow_through_delay * length_of_loop
        time_offset = i * follow_through_secs

        for t in times:
            # Effective time for the sine wave
            t_eff = t - time_offset
            
            # Adjust B curl with an offset double-paced sine wave to allow for tail uncurling at each peak of the wag
            extend_sine = math.sin(omega * t_eff * 2 + follow_through_secs * 0.3 * (i-1)) # don't question it
            extend_sine = (extend_sine+1)/2 # map to 0-1
            extend_sine = 1-pow(1-extend_sine, 1.5) # trust me bro, this helps i swear
            bone_curl_B = bone_curl_B_min + extend_sine * (bone_curl_B_max - bone_curl_B_min) # set the final curl_B (with wave mapped from 0-1 to B_min - B_max)
            
        
            if (i == 0):
                base_x = root_angle
                base_y = 0
                base_z = 0
            else:
                base_x = pow(float(i), bone_curl_A_exponent) * bone_curl_A
                base_y = 0
                base_z = 0
                base_x += pow(float(i), bone_curl_B_exponent) * bone_curl_B
                base_y += 0
                base_z += 0


            # Side-to-side wag on the Z axis
            wave_z = sway_amount * math.sin(omega * t_eff) * ((3.0+i)/6)

            # Final angles = base pose + wave
            x_val = base_x
            y_val = base_y
            z_val = base_z + wave_z

            euler_keyframes[bone].append((t, (x_val, y_val, z_val)))
            editor_curves[bone]['x'].append((t, x_val))
            editor_curves[bone]['y'].append((t, y_val))
            editor_curves[bone]['z'].append((t, z_val))



    # --------------------------------------------------------------------------------
    # 3) BUILD YAML
    # --------------------------------------------------------------------------------
    filename = output_path.replace('\\', '/').split('/')[-1].split('.')[0]
    
    yaml_lines = []
    yaml_lines.append("%YAML 1.1")
    yaml_lines.append("%TAG !u! tag:unity3d.com,2011:")
    yaml_lines.append("--- !u!74 &7400000")
    yaml_lines.append("AnimationClip:")
    yaml_lines.append("  m_ObjectHideFlags: 0")
    yaml_lines.append("  m_CorrespondingSourceObject: {fileID: 0}")
    yaml_lines.append("  m_PrefabInstance: {fileID: 0}")
    yaml_lines.append("  m_PrefabAsset: {fileID: 0}")
    yaml_lines.append(f"  m_Name: {filename}")
    yaml_lines.append("  serializedVersion: 6")

    # If you want the new system, keep 0. If you want quick path-based binding, set 1:
    yaml_lines.append(f"  m_Legacy: 0")
    yaml_lines.append("  m_Compressed: 0")
    yaml_lines.append("  m_UseHighQualityCurve: 1")
    yaml_lines.append("  m_RotationCurves: []")
    yaml_lines.append("  m_CompressedRotationCurves: []")

    # A) m_EulerCurves: store the X/Y/Z in a single curve structure per bone
    yaml_lines.append("  m_EulerCurves:")
    for bone_path in tail_bones:
        yaml_lines.append("  - curve:")
        yaml_lines.append("      serializedVersion: 2")
        yaml_lines.append("      m_Curve:")
        for (time_val, (xv, yv, zv)) in euler_keyframes[bone_path]:
            yaml_lines.append("      - serializedVersion: 3")
            yaml_lines.append(f"        time: {time_val}")
            yaml_lines.append(f"        value: {{x: {xv}, y: {yv}, z: {zv}}}")
            yaml_lines.append("        inSlope: {x: 0, y: 0, z: 0}")
            yaml_lines.append("        outSlope: {x: 0, y: 0, z: 0}")
            yaml_lines.append("        tangentMode: 1")
            yaml_lines.append("        weightedMode: 0")
            yaml_lines.append("        inWeight: {x: 0.33333334, y: 0.33333334, z: 0.33333334}")
            yaml_lines.append("        outWeight: {x: 0.33333334, y: 0.33333334, z: 0.33333334}")
        yaml_lines.append("      m_PreInfinity: 2")
        yaml_lines.append("      m_PostInfinity: 2")
        yaml_lines.append("      m_RotationOrder: 4")
        yaml_lines.append(f"    path: {bone_path}")

    # If you want to animate local position too, replicate it here
    yaml_lines.append("  m_PositionCurves: []")
    yaml_lines.append("  m_ScaleCurves: []")
    yaml_lines.append("  m_FloatCurves: []")
    yaml_lines.append("  m_PPtrCurves: []")
    yaml_lines.append("  m_SampleRate: 60")
    yaml_lines.append("  m_WrapMode: 0")

    # Bounds
    yaml_lines.append("  m_Bounds:")
    yaml_lines.append("    m_Center: {x: 0, y: 0, z: 0}")
    yaml_lines.append("    m_Extent: {x: 0, y: 0, z: 0}")

    # m_ClipBindingConstant:
    # Non-legacy must have hashed references for each bone's rotation
    yaml_lines.append("  m_ClipBindingConstant:")
    yaml_lines.append("    genericBindings:")
    for i, bone_path in enumerate(tail_bones):
        hashed = unity_string_to_hash(bone_path)
        yaml_lines.append("    - serializedVersion: 2")
        yaml_lines.append(f"      path: {hashed}")
        yaml_lines.append("      attribute: 4")  # rotation
        yaml_lines.append("      script: {fileID: 0}")
        yaml_lines.append("      typeID: 4")
        yaml_lines.append("      customType: 4")  # euler
        yaml_lines.append("      isPPtrCurve: 0")
    yaml_lines.append("    pptrCurveMapping: []")

    # Clip settings
    yaml_lines.append("  m_AnimationClipSettings:")
    yaml_lines.append("    serializedVersion: 2")
    yaml_lines.append("    m_AdditiveReferencePoseClip: {fileID: 0}")
    yaml_lines.append("    m_AdditiveReferencePoseTime: 0")
    yaml_lines.append("    m_StartTime: 0")
    yaml_lines.append(f"    m_StopTime: {length_of_loop}")
    yaml_lines.append("    m_OrientationOffsetY: 0")
    yaml_lines.append("    m_Level: 0")
    yaml_lines.append("    m_CycleOffset: 0")
    yaml_lines.append("    m_HasAdditiveReferencePose: 0")
    yaml_lines.append("    m_LoopTime: 1")
    yaml_lines.append("    m_LoopBlend: 0")
    yaml_lines.append("    m_LoopBlendOrientation: 0")
    yaml_lines.append("    m_LoopBlendPositionY: 0")
    yaml_lines.append("    m_LoopBlendPositionXZ: 0")
    yaml_lines.append("    m_KeepOriginalOrientation: 0")
    yaml_lines.append("    m_KeepOriginalPositionY: 1")
    yaml_lines.append("    m_KeepOriginalPositionXZ: 0")
    yaml_lines.append("    m_HeightFromFeet: 0")
    yaml_lines.append("    m_Mirror: 0")

    # m_EditorCurves (per-axis for the editor)
    yaml_lines.append("  m_EditorCurves:")

    def write_editor_curve(curve_tuples, attribute, path):
        yaml_lines.append("  - curve:")
        yaml_lines.append("      serializedVersion: 2")
        yaml_lines.append("      m_Curve:")
        for (t, val) in curve_tuples:
            yaml_lines.append("      - serializedVersion: 3")
            yaml_lines.append(f"        time: {t}")
            yaml_lines.append(f"        value: {val}")
            yaml_lines.append("        inSlope: 0")
            yaml_lines.append("        outSlope: 0")
            yaml_lines.append("        tangentMode: 1")
            yaml_lines.append("        weightedMode: 0")
            yaml_lines.append("        inWeight: 0.33333334")
            yaml_lines.append("        outWeight: 0.33333334")
        yaml_lines.append("      m_PreInfinity: 2")
        yaml_lines.append("      m_PostInfinity: 2")
        yaml_lines.append("      m_RotationOrder: 4")
        yaml_lines.append(f"    attribute: {attribute}")
        yaml_lines.append(f"    path: {path}")
        yaml_lines.append("    classID: 4")
        yaml_lines.append("    script: {fileID: 0}")

    for bone_path in tail_bones:
        # x
        write_editor_curve(editor_curves[bone_path]['x'], "localEulerAnglesRaw.x", bone_path)
        # y
        write_editor_curve(editor_curves[bone_path]['y'], "localEulerAnglesRaw.y", bone_path)
        # z  
        write_editor_curve(editor_curves[bone_path]['z'], "localEulerAnglesRaw.z", bone_path)

    # m_EulerEditorCurves: original pattern of empty arrays
    yaml_lines.append("  m_EulerEditorCurves:")
    yaml_lines.append("  - curve:")
    yaml_lines.append("      serializedVersion: 2")
    yaml_lines.append("      m_Curve: []")
    yaml_lines.append("      m_PreInfinity: 2")
    yaml_lines.append("      m_PostInfinity: 2")
    yaml_lines.append("      m_RotationOrder: 4")
    yaml_lines.append(f"    attribute: m_LocalEulerAngles.x")
    yaml_lines.append(f"    path: {tail_bones[0]}")
    yaml_lines.append("    classID: 4")
    yaml_lines.append("    script: {fileID: 0}")
    yaml_lines.append("  - curve:")
    yaml_lines.append("      serializedVersion: 2")
    yaml_lines.append("      m_Curve: []")
    yaml_lines.append("      m_PreInfinity: 2")
    yaml_lines.append("      m_PostInfinity: 2")
    yaml_lines.append("      m_RotationOrder: 4")
    yaml_lines.append(f"    attribute: m_Local")
    yaml_lines.append(f"    attribute: m_LocalEulerAngles.y")
    yaml_lines.append(f"    path: {tail_bones[0]}")
    yaml_lines.append("    classID: 4")
    yaml_lines.append("    script: {fileID: 0}")
    yaml_lines.append("  - curve:")
    yaml_lines.append("      serializedVersion: 2")
    yaml_lines.append("      m_Curve: []")
    yaml_lines.append("      m_PreInfinity: 2")
    yaml_lines.append("      m_PostInfinity: 2")
    yaml_lines.append("      m_RotationOrder: 4")
    yaml_lines.append(f"    attribute: m_LocalEulerAngles.z")
    yaml_lines.append(f"    path: {tail_bones[0]}")
    yaml_lines.append("    classID: 4")
    yaml_lines.append("    script: {fileID: 0}")

    yaml_lines.append("  m_HasGenericRootTransform: 0")
    yaml_lines.append("  m_HasMotionFloatCurves: 0")
    yaml_lines.append("  m_Events: []")

    # Write output file
    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(yaml_lines))
    print(f"Animation saved to {output_path}")

def unity_string_to_hash(input_string: str) -> int:
    """
    Emulates Unity's Animator.StringToHash using a table-based CRC32 implementation.
    (big thanks to some random Unity staff member on some forum mentioning off-hand that they use CRC32 for the path hashes)
    """
    # Data to hash
    data = input_string.encode('utf-8')

    # Generate the CRC32 lookup table ---
    polynomial = 0xEDB88320
    crc32_table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ polynomial
            else:
                crc >>= 1
        crc32_table.append(crc)

    # Calculate the CRC32 using the table ---
    crc = 0xFFFFFFFF
    for b in data:
        crc = (crc >> 8) ^ crc32_table[(crc ^ b) & 0xFF]

    # Final XOR to invert bits and ensure unsigned
    crc = crc ^ 0xFFFFFFFF

    # Mask to 32 bits (unsigned)
    return crc & 0xFFFFFFFF

if __name__ == "__main__":
    main()