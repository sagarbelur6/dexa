import re
import json
import xmltodict
import pandas as pd
from pathlib import Path
import os
import logging 
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DEXA_KNOWLEDGE_BASE_PATH = "D:\\dexa\\knowledge base\\dexa_kb.md"


def setup_logger(log_path):
    logger = logging.getLogger(str(log_path))
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    fh = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def transform_dexa_ruleset(df, dexa_kb, api_key, logger=None, file_dir=None):
    if logger:
        logger.info("Starting DEXA JavaScript transformation...")

    client = OpenAI(api_key=api_key)

    if "Dexa JS Logic" not in df.columns:
        df["Dexa JS Logic"] = ""
        if logger:
            logger.info("Added 'Dexa JS Logic' column to DataFrame.")

    if "Is Processed" not in df.columns:
        df["Is Processed"] = ""
        if logger:
            logger.info("Added 'Is Processed' column to DataFrame.")

    valid_rows = df[
        (df["Transformation Logic"].str.lower() == "extended rule") &
        (df["Extracted Logic (Raw)"].notna()) &
        ((df["Dexa JS Logic"].isna()) | (df["Dexa JS Logic"].str.strip() == "")) &
        ((df["Is Processed"].isna()) | (df["Is Processed"].str.strip() == ""))
    ].copy()

    if logger:
        logger.info(f"Found {len(valid_rows)} rows to process for DEXA transformation.")

    all_rules = [
        str(row["Extracted Logic (Raw)"]).strip()
        for _, row in valid_rows.iterrows()
        if pd.notna(row["Extracted Logic (Raw)"])
    ]
    first_10_rules = all_rules[:10]
    declared_variables = extract_dexa_variables_from_all_rules(first_10_rules, client, file_dir)

    if logger:
        logger.info(f"Extracted declared JS variables:\n{declared_variables}")

    system_prompt = f"""
You are a JavaScript expert working on a data transformation engine called DEXA.
You help convert raw transformation rules into JavaScript logic.

Guidelines:
- Always output valid, executable JavaScript.
- Response format:
{{
  "js": "<JavaScript transformation logic>"
}}
- DO NOT wrap your response in markdown (like ```json).
- DO NOT explain anything. No comments or helper text.
- Use 'tmp' as the output object and 'msg' as the input.
- If the logic cannot be interpreted, return the original rule as-is.

Knowledge Base:
{dexa_kb}
"""

    for idx, row in valid_rows.iterrows():
        rule = str(row["Extracted Logic (Raw)"],).strip()
        input_desc = row.get("Source Field Description", "")
        source_field = row.get("Source XML Node/Element", "") or row.get("Source Field", "")
        target_field = row.get("Target Element", "") or row.get("Target Field", "")
        execution_type = str(row.get("Execution Type", "")).strip().lower()

        if logger:
            logger.info(f"Processing row {idx} | Execution Type: {execution_type}")

        if execution_type == "presession":
            df.at[idx, "Dexa JS Logic"] = "// Pre-session logic handled separately"
            df.at[idx, "Is Processed"] = "YES"
            if logger:
                logger.info(f"Row {idx}: Set preSession flag.")
            continue

        user_prompt = f"""
Transform the following business logic into a JavaScript function suitable for a data integration engine like DEXA.

Context:
- Input Field: {source_field}
- Output Field: {target_field}
- Input Description: {input_desc}
- Raw Logic: {rule}

Return the JavaScript code in this format:
{{
  "js": "<logic here>"
}}

DO NOT wrap in markdown. DO NOT include any explanation. Just return valid JSON.
"""

        try:
            if logger:
                logger.info(f"Sending rule for row {idx} to OpenAI API.")

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()

            if content.startswith("```"):
                content = content.strip("`").strip()

            try:
                js_output = json.loads(content)
                js_code = js_output.get("js", "").strip()

                if js_code and "tmp" not in js_code:
                    js_code = f"let tmp = {{}};\nlet msg = inputMessage;\n{js_code}"

                if js_code:
                    df.at[idx, "Dexa JS Logic"] = js_code
                    df.at[idx, "Is Processed"] = "YES"
                    if logger:
                        logger.info(f"Row {idx}: JS logic updated.")
            except Exception as parse_err:
                df.at[idx, "Dexa JS Logic"] = f"// Error parsing response: {parse_err}\\n// Raw: {content}"
                if logger:
                    logger.error(f"JSON parse error for rule {idx}: {parse_err}")
        except Exception as e:
            df.at[idx, "Dexa JS Logic"] = f"// API error: {e}"
            if logger:
                logger.error(f"API error for rule {idx}: {e}")

def extract_dexa_variables_from_all_rules(rules: list[str], client, file_dir: Path) -> str:
    """
    Extracts JavaScript variable declarations used in transformation rules using OpenAI.
    Saves the result as 'dexa_extracted_variables.js' in the given directory.
    """
    full_input = "\n\n".join(rules)

    prompt = f"""
You are a JavaScript code expert working for a transformation engine called DEXA.

From the following transformation rules, extract all variable declarations and initializations.

✅ Strict instructions:
- Use 'let' or 'const' with appropriate default values.
- No duplicate declarations.
- No transformation logic, no functions, no conditions.
- Output ONLY variable declarations.

Rules:
{full_input}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You extract JavaScript variable declarations for DEXA."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        variables = sorted(set(line.strip() for line in content.splitlines() if line.strip().startswith(("let ", "const "))))
        variables_str = "\n".join(variables)

        output_path = file_dir / "dexa_extracted_variables.js"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(variables_str)

        return variables_str

    except Exception as e:
        print(f"❌ Failed to extract variable declarations: {e}")
        return ""
    
    
def extract_outbound_extended_rules_from_xml(xml_path):
    with open(xml_path, "r", encoding="utf-8") as f:
        xml_data = xmltodict.parse(f.read())

    extended_rules = {
        "preSession": "",
        "postSession": "",
        "input": [],
        "output": []
    }

    def collect_rule(target, rule_type, context, rule, data_type):
        if rule and rule.strip():
            extended_rules[target].append({
                "type": rule_type,
                "context": context,
                "rule": rule.strip(),
                "data_type": data_type
            })

    def get_element_rules(field_list, segment_name, is_output=False, group_name=""):
        if not field_list:
            return
        fields = field_list if isinstance(field_list, list) else [field_list]
        for field in fields:
            context = f"{segment_name}.{field['Name']}" if is_output else f"{group_name}.{field['Name']}"
            rule = field.get("ExplicitRule")
            dataType = field.get("StoreLimit", {}).get("DataType", "").capitalize()
            if rule:
                active = field.get("@Active") or field.get("Active")
                if active == "1":
                    collect_rule("output" if is_output else "input", "inline", context, rule.strip(), dataType)

    def extract_all_input_rules(group):
        group_name = group.get("Name", "")
        rule = group.get("ExplicitRule", {})
        if isinstance(rule, dict):
            collect_rule("output", "onBegin", group_name, rule.get("OnBegin", ""), '')
            collect_rule("output", "onEnd", group_name, rule.get("OnEnd", ""), '')

        segments = group.get("Segment")
        if segments:
            segments = segments if isinstance(segments, list) else [segments]
            for segment in segments:
                seg_name = segment.get("Name", "")
                rule = segment.get("ExplicitRule", {})
                if isinstance(rule, dict):
                    collect_rule("output", "onBegin", seg_name, rule.get("OnBegin", ""), '')
                    collect_rule("output", "onEnd", seg_name, rule.get("OnEnd", ""), '')
                get_element_rules(segment.get("Field"), seg_name, True)

        nested = group.get("Group")
        if nested:
            nested = nested if isinstance(nested, list) else [nested]
            for sub in nested:
                extract_all_input_rules(sub)

    def extract_output_rules(group_list):
        def walk(groups):
            if isinstance(groups, dict):
                groups = [groups]
            for group in groups:
                group_name = group.get("Name", "")
                group_rule = group.get("ExplicitRule", {})
                if isinstance(group_rule, dict):
                    collect_rule("input", "onBegin", group_name, group_rule.get("OnBegin", ""), '')
                    collect_rule("input", "onEnd", group_name, group_rule.get("OnEnd", ""), '')

                record = group.get("XMLRecord")
                if record:
                    get_element_rules(record.get("Field"), record.get("Name"), False, group_name)
                    rule = record.get("ExplicitRule", {})
                    if isinstance(rule, dict):
                        collect_rule("input", "onBegin", group_name, rule.get("OnBegin", ""), '')
                        collect_rule("input", "onEnd", group_name, rule.get("OnEnd", ""), '')

                nested = group.get("XMLParticleGroup")
                if nested:
                    walk(nested)
                nested_elem = group.get("XMLElementGroup")
                if nested_elem:
                    walk(nested_elem)

        walk(group_list)

    def extract_session_rules(mapper):
        rule = mapper.get("MapDetails", {}).get("ExplicitRule", {})
        if isinstance(rule, dict):
            extended_rules["preSession"] = rule.get("PreSessionRule", "").strip()
            extended_rules["postSession"] = rule.get("PostSessionRule", "").strip()

    mapper = xml_data.get("Mapper", {})
    extract_session_rules(mapper)

    input_group = mapper.get("INPUT", {}).get("XMLSyntax", {}).get("XMLElementGroup")
    if input_group:
        extract_output_rules(input_group)

    output_group = mapper.get("OUTPUT", {}).get("EDISyntax", {}).get("Group")
    if output_group:
        extract_all_input_rules(output_group)

    return extended_rules

def extract_inbound_extended_rules_from_xml(xml_path):
    with open(xml_path, "r", encoding="utf-8") as f:
        xml_data = xmltodict.parse(f.read())

    extended_rules = {
        "preSession": "",
        "postSession": "",
        "input": [],
        "output": []
    }

    def collect_rule(target, rule_type, context, rule, data_type):
        if rule and rule.strip():
            extended_rules[target].append({
                "type": rule_type,
                "context": context,
                "rule": rule.strip(),
                "data_type": data_type
            })

    def get_element_rules(field_list, segment_name, is_output=False, group_name=""):
        if not field_list:
            return
        fields = field_list if isinstance(field_list, list) else [field_list]
        for field in fields:
            context = f"{group_name}.{field['Name']}" if is_output else f"{segment_name}.{field['Name']}"
            rule = field.get("ExplicitRule")
            dataType = field.get("StoreLimit", {}).get("DataType", "").capitalize()
            if rule:
                active = field.get("@Active") or field.get("Active")
                if active == "1":
                    collect_rule("output" if is_output else "input", "inline", context, rule.strip(), dataType)

    def extract_all_input_rules(group):
        group_name = group.get("Name", "")
        rule = group.get("ExplicitRule", {})
        if isinstance(rule, dict):
            collect_rule("input", "onBegin", group_name, rule.get("OnBegin", ""), '')
            collect_rule("input", "onEnd", group_name, rule.get("OnEnd", ""), '')

        segments = group.get("Segment")
        if segments:
            segments = segments if isinstance(segments, list) else [segments]
            for segment in segments:
                seg_name = segment.get("Name", "")
                rule = segment.get("ExplicitRule", {})
                if isinstance(rule, dict):
                    collect_rule("input", "onBegin", seg_name, rule.get("OnBegin", ""), '')
                    collect_rule("input", "onEnd", seg_name, rule.get("OnEnd", ""), '')
                get_element_rules(segment.get("Field"), seg_name, False)

        nested = group.get("Group")
        if nested:
            nested = nested if isinstance(nested, list) else [nested]
            for sub in nested:
                extract_all_input_rules(sub)

    def extract_output_rules(group_list):
        def walk(groups):
            groups = groups if isinstance(groups, list) else [groups]
            for group in groups:
                group_name = group.get("Name", "")
                record = group.get("XMLRecord")
                if record:
                    get_element_rules(record.get("Field"), record.get("Name"), True, group_name)
                    rule = record.get("ExplicitRule", {})
                    if isinstance(rule, dict):
                        collect_rule("output", "onBegin", group_name, rule.get("OnBegin", ""), '')
                        collect_rule("output", "onEnd", group_name, rule.get("OnEnd", ""), '')
                nested = group.get("XMLParticleGroup", {}).get("XMLElementGroup")
                if nested:
                    walk(nested)

        walk(group_list)

    def extract_session_rules(mapper):
        rule = mapper.get("MapDetails", {}).get("ExplicitRule", {})
        if isinstance(rule, dict):
            extended_rules["preSession"] = rule.get("PreSessionRule", "").strip()
            extended_rules["postSession"] = rule.get("PostSessionRule", "").strip()

    mapper = xml_data.get("Mapper", {})
    extract_session_rules(mapper)

    input_group = mapper.get("INPUT", {}).get("EDISyntax", {}).get("Group")
    if input_group:
        extract_all_input_rules(input_group)

    output_group = mapper.get("OUTPUT", {}).get("XMLSyntax", {}).get("XMLElementGroup")
    if output_group:
        extract_output_rules(output_group)

    return extended_rules


def extract_mapping_lines(file_path, start, end):
    with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
        lines = f.readlines()

    section_lines = []
    in_section = False

    for line in lines:
        trimmed = line.strip()
        if trimmed == start:
            in_section = True
            continue
        if trimmed == end and in_section:
            break
        if in_section:
            section_lines.append(trimmed)

    return section_lines
def parse_inbound_mappings(lines):
    result = []
    current_segment = None
    for line in lines:
        seg_match = re.match(r"^(?:Element|Segment)\s+(\w+)(?::(\d+))?\*", line)
        if seg_match:
            current_segment = seg_match.group(1)
            if seg_match.group(2):
                current_segment += f":{seg_match.group(2)}"
            result.append({"segment": current_segment, "mappings": [], "outputSegment": ""})
            continue

        map_match = re.match(r"^\s*(?:(\w+(?::\d+)?)\*\s+)?----->\s+([\w:]+)\*\s+([\w\d:-]+)", line)
        if map_match and current_segment:
            last = result[-1]
            raw_input = (
                map_match.group(1)
                if map_match.group(1)
                else (
                    f"{last['mappings'][-1]['input']}:{last['mappings'][-1]['inputOccurrence']}"
                    if last['mappings']
                    else ""
                )
            )
            input_part = raw_input.split(":")
            output_segment = map_match.group(2).strip()
            output_part = map_match.group(3).strip().split(":")

            last["outputSegment"] = output_segment
            last["mappings"].append({
                "input": input_part[0],
                "inputOccurrence": input_part[1] if len(input_part) > 1 else None,
                "outputElement": output_part[0],
                "outputSegment": output_segment,
                "outputOccurrence": output_part[1] if len(output_part) > 1 else None
            })
    return result


def parse_outbound_mappings(lines):
    result = []
    current_segment = None
    for line in lines:
        seg_match = re.match(r"^Element ([\w:]+)\*", line)
        if seg_match:
            current_segment = seg_match.group(1)
            result.append({"segment": current_segment, "mappings": [], "outputSegment": ""})
            continue

        map_match = re.match(r"^\s*(?:(\w+(?::\d+)?)\*\s+)?----->\s+([\w:]+)\*\s+([\w\d:-]+)", line)
        if map_match and current_segment:
            last = result[-1]
            raw_input = (
                map_match.group(1).strip()
                if map_match.group(1)
                else (
                    f"{last['mappings'][-1]['input']}:{last['mappings'][-1]['inputOccurrence']}"
                    if last['mappings'] and last['mappings'][-1]['input']
                    else ""
                )
            )
            input_part = raw_input.split(":")
            output_segment = map_match.group(2).strip()
            output_part = map_match.group(3).strip().split(":")

            last["outputSegment"] = output_segment
            last["mappings"].append({
                "input": input_part[0],
                "inputOccurrence": input_part[1] if len(input_part) > 1 else None,
                "outputElement": output_part[0],
                "outputSegment": output_segment,
                "outputOccurrence": output_part[1] if len(output_part) > 1 else None
            })
    return result


def find_element_details(records, segment_name, element_id):
    seg_clean = segment_name.replace("*", "").replace("_attr_", "")
    el_clean = element_id.replace("*", "").replace("_attr_", "")

    for segment in records:
        if segment["segment"].replace("*", "").replace("_attr_", "") == seg_clean:
            for el in segment.get("elements", []):
                if el["elementID"].replace("*", "").replace("_attr_", "") == el_clean:
                    return el
    return {}

def parse_outbound_record_details_from_xml():
    with open(XML_FILE, "r", encoding="utf-8") as f:
        xml_dict = xmltodict.parse(f.read())

    mapper = xml_dict.get("Mapper", {})

    def extract_input_segments(group):
        segments = []
        if isinstance(group, list):
            for g in group:
                segments += extract_input_segments(g)
        else:
            if "Segment" in group:
                segs = group["Segment"]
                segments += segs if isinstance(segs, list) else [segs]
            if "Group" in group:
                segments += extract_input_segments(group["Group"])
        return segments

    input_groups = mapper.get("OUTPUT", {}).get("EDISyntax", {}).get("Group", {})
    raw_input_segments = extract_input_segments(input_groups)

    def format_segment(seg):
        fields = seg.get("Field", [])
        if isinstance(fields, dict):
            fields = [fields]
        return {
            "segment": seg.get("Name", ""),
            "tag": seg.get("Name", "") + "*",
            "requirement": "Mandatory" if seg.get("Min") == "1" else "Conditional",
            "minUse": int(seg.get("Min", 0)),
            "maxUse": int(seg.get("Max", 1)),
            "description": seg.get("Description", ""),
            "elements": [
                {
                    "elementID": f.get("Name", "") + "*",
                    "description": f.get("Description", ""),
                    "requirement": "M" if f.get("Mandatory", "").lower() == "yes" else "C",
                    "minLength": int(f.get("StoreLimit", {}).get("MinLen", 0)),
                    "maxLength": int(f.get("StoreLimit", {}).get("MaxLen", 0)),
                    "dataType": f.get("StoreLimit", {}).get("DataType", "string").capitalize(),
                    "format": f.get("StoreLimit", {}).get("Format"),
                    "notes": None
                }
                for f in fields
            ]
        }

    input_record_details = [format_segment(seg) for seg in raw_input_segments]

    def extract_output_segments(groups):
        segments = []
        for group in groups if isinstance(groups, list) else [groups]:
            if "XMLRecord" in group:
                record = group["XMLRecord"]
                fields = record.get("Field", [])
                if isinstance(fields, dict):
                    fields = [fields]
                segments.append({
                    "segment": record.get("Name", ""),
                    "tag": (record.get("Tag") or record.get("Name", "")) + "*",
                    "requirement": "Mandatory" if record.get("Min") == "1" else "Conditional",
                    "minUse": int(record.get("Min", 0)),
                    "maxUse": int(record.get("Max", 1)),
                    "description": record.get("Description", ""),
                    "elements": [
                        {
                            "elementID": f.get("Name", "") + "*",
                            "description": f.get("Description", ""),
                            "requirement": "M" if f.get("Mandatory", "").lower() == "yes" else "C",
                            "minLength": int(f.get("StoreLimit", {}).get("MinLen", 0)),
                            "maxLength": int(f.get("StoreLimit", {}).get("MaxLen", 0)),
                            "dataType": f.get("StoreLimit", {}).get("DataType", "string").capitalize(),
                            "format": f.get("StoreLimit", {}).get("Format"),
                            "notes": None
                        }
                        for f in fields
                    ]
                })
            if "XMLParticleGroup" in group and "XMLElementGroup" in group["XMLParticleGroup"]:
                segments.extend(extract_output_segments(group["XMLParticleGroup"]["XMLElementGroup"]))
        return segments

    output_groups = mapper.get("INPUT", {}).get("XMLSyntax", {}).get("XMLElementGroup", {})
    output_record_details = extract_output_segments(output_groups)

    return output_record_details, input_record_details

def detect_mode_and_transaction(filename):
    filename = filename.upper()

    if "_IN." in filename or "_IN_" in filename or "_IN-" in filename:
        mode = "inbound"
    elif "_OUT." in filename or "_OUT_" in filename or "_OUT-" in filename:
        mode = "outbound"
    else:
        raise ValueError("❌ TXT file name must contain 'IN' or 'OUT' to determine mode.")

    match = re.search(r'_(\d{3})(?:_|\.|$)', filename)
    transaction_type = match.group(1) if match else None

    return mode, transaction_type

def parse_inbound_record_details_from_xml():
    with open(XML_FILE, "r", encoding="utf-8") as f:
        xml_dict = xmltodict.parse(f.read())

    mapper = xml_dict.get("Mapper", {})

    def extract_input_segments(group):
        segments = []
        if isinstance(group, list):
            for g in group:
                segments += extract_input_segments(g)
        else:
            if "Segment" in group:
                segs = group["Segment"]
                segments += segs if isinstance(segs, list) else [segs]
            if "Group" in group:
                segments += extract_input_segments(group["Group"])
        return segments

    input_groups = mapper.get("INPUT", {}).get("EDISyntax", {}).get("Group", {})
    raw_input_segments = extract_input_segments(input_groups)

    def format_segment(seg):
        fields = seg.get("Field", [])
        if isinstance(fields, dict):
            fields = [fields]
        return {
            "segment": seg.get("Name", ""),
            "tag": seg.get("Name", "") + "*",
            "requirement": "Mandatory" if seg.get("Min") == "1" else "Conditional",
            "minUse": int(seg.get("Min", 0)),
            "maxUse": int(seg.get("Max", 1)),
            "description": seg.get("Description", ""),
            "elements": [
                {
                    "elementID": f.get("Name", "") + "*",
                    "description": f.get("Description", ""),
                    "requirement": "M" if f.get("Mandatory", "").lower() == "yes" else "C",
                    "minLength": int(f.get("StoreLimit", {}).get("MinLen", 0)),
                    "maxLength": int(f.get("StoreLimit", {}).get("MaxLen", 0)),
                    "dataType": f.get("StoreLimit", {}).get("DataType", "string").capitalize(),
                    "format": f.get("StoreLimit", {}).get("Format"),
                    "notes": None
                }
                for f in fields
            ]
        }

    input_record_details = [format_segment(seg) for seg in raw_input_segments]

    def extract_output_segments(groups):
        segments = []
        for group in groups if isinstance(groups, list) else [groups]:
            if "XMLRecord" in group:
                record = group["XMLRecord"]
                fields = record.get("Field", [])
                if isinstance(fields, dict):
                    fields = [fields]
                segments.append({
                    "segment": record.get("Name", ""),
                    "tag": (record.get("Tag") or record.get("Name", "")) + "*",
                    "requirement": "Mandatory" if record.get("Min") == "1" else "Conditional",
                    "minUse": int(record.get("Min", 0)),
                    "maxUse": int(record.get("Max", 1)),
                    "description": record.get("Description", ""),
                    "elements": [
                        {
                            "elementID": f.get("Name", "") + "*",
                            "description": f.get("Description", ""),
                            "requirement": "M" if f.get("Mandatory", "").lower() == "yes" else "C",
                            "minLength": int(f.get("StoreLimit", {}).get("MinLen", 0)),
                            "maxLength": int(f.get("StoreLimit", {}).get("MaxLen", 0)),
                            "dataType": f.get("StoreLimit", {}).get("DataType", "string").capitalize(),
                            "format": f.get("StoreLimit", {}).get("Format"),
                            "notes": None
                        }
                        for f in fields
                    ]
                })
            if "XMLParticleGroup" in group and "XMLElementGroup" in group["XMLParticleGroup"]:
                nested = group["XMLParticleGroup"]["XMLElementGroup"]
                segments.extend(extract_output_segments(nested))
        return segments

    output_groups = mapper.get("OUTPUT", {}).get("XMLSyntax", {}).get("XMLElementGroup", {})
    output_record_details = extract_output_segments(output_groups)

    return input_record_details, output_record_details

def process_file_pair(txt_file, xml_file):
    log_path = txt_file.parent / "mrs_generation_log.log"
    logger = setup_logger(log_path)

    try:
        mode, transaction_type = detect_mode_and_transaction(txt_file.name)
        logger.info(f"Processing: {txt_file} | {xml_file} | Mode: {mode} | Transaction: {transaction_type}")

        global MODE, TXT_FILE, XML_FILE
        MODE = mode
        TXT_FILE = txt_file
        XML_FILE = xml_file

        base_name = TXT_FILE.stem.replace("PTFFormat_", "")
        output_excel_path = TXT_FILE.parent / f"{base_name}__MRS_Doc.xlsx"

        logger.info(f"Extracting mapping lines from {TXT_FILE}")
        extract_func = parse_inbound_mappings if MODE == "inbound" else parse_outbound_mappings
        mapping_lines = extract_mapping_lines(TXT_FILE, "Mapping Information", "Extended Rules")
        mappings = extract_func(mapping_lines)
        logger.info(f"Found {len(mappings)} mapping groups.")

        if MODE == 'inbound':
            logger.info(f"Extracting inbound extended rules from {XML_FILE}")
            extended = extract_inbound_extended_rules_from_xml(XML_FILE)
            input_records, output_records = parse_inbound_record_details_from_xml()
        else:
            logger.info(f"Extracting outbound extended rules from {XML_FILE}")
            extended = extract_outbound_extended_rules_from_xml(XML_FILE)
            input_records, output_records = parse_outbound_record_details_from_xml()

        rows = []
        for group in mappings:
            for map in group["mappings"]:
                input_occ = map.get('inputOccurrence')
                input_id = f"{map['input']}{':' + str(input_occ) if input_occ not in (None, 'None', '') else ''}"
                output_id = f"{map['outputElement']}{':' + map['outputOccurrence'] if map['outputOccurrence'] else ''}"
                input_meta = find_element_details(input_records, group["segment"], input_id)
                output_meta = find_element_details(output_records, map["outputSegment"], output_id)
                rows.append({
                    'Major Section': group["segment"],
                    'Source XML Node/Element': input_id,
                    'Source Field Description': input_meta.get("description", ""),
                    'Mandatory/Optional (M/C)': input_meta.get("requirement", ""),
                    'Source Data Type': input_meta.get("dataType", ""),
                    'Source Min Length': input_meta.get("minLength"),
                    'Source Max Length': input_meta.get("maxLength"),
                    'Target Segment': map["outputSegment"],
                    'Target Element': output_id,
                    'Target Description': output_meta.get("description", ""),
                    'Target Mandatory/Optional (M/C)': output_meta.get("requirement", ""),
                    'Target Data Type': output_meta.get("dataType", ""),
                    'Target Min Length': output_meta.get("minLength"),
                    'Target Max Length': output_meta.get("maxLength"),
                    'Transformation Logic': 'Direct Mapping'
                })

        logger.info(f"Added {len(rows)} direct mapping rows.")

        if extended.get("preSession"):
            logger.info("Adding preSession extended rule.")
            rows.append({
                'Transformation Logic': "Extended Rule",
                'Execution Type': "preSession",
                'Extracted Logic (Raw)': extended["preSession"]
            })
        if extended.get("postSession"):
            logger.info("Adding postSession extended rule.")
            rows.append({
                'Transformation Logic': "Extended Rule",
                'Execution Type': "postSession",
                'Extracted Logic (Raw)': extended["postSession"]
            })

        for rule in extended.get("input", []):
            parts = rule["context"].split(".")
            seg = parts[0]
            fld = parts[1] if len(parts) > 1 else ""
            rows.append({
                'Major Section': seg,
                'Source XML Node/Element': fld,
                'Transformation Logic': "Extended Rule",
                'Source Data Type': rule["data_type"],
                'Execution Type': rule["type"],
                'Extracted Logic (Raw)': rule["rule"]
            })

        for rule in extended.get("output", []):
            parts = rule["context"].split(".")
            seg = parts[0]
            fld = parts[1] if len(parts) > 1 else ""
            rows.append({
                'Target Segment': seg,
                'Target Element': fld,
                'Transformation Logic': "Extended Rule",
                'Target Data Type': rule["data_type"],
                'Execution Type': rule["type"],
                'Extracted Logic (Raw)': rule["rule"]
            })

        logger.info(f"Total rows to write: {len(rows)}")
        df = pd.DataFrame(rows)

        with open(DEXA_KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            dexa_kb = f.read()

        api_key = os.getenv("OPENAI_API_KEY")
        transform_dexa_ruleset(df, dexa_kb, api_key, logger, TXT_FILE.parent)

        df.to_excel(output_excel_path, index=False, sheet_name="DexaTransform")
        logger.info(f"✅ DEXA transform mapping saved to {output_excel_path}")

    except Exception as e:
        logger.error(f"❌ Failed to process {txt_file}: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Update path as needed
    input_dir = Path(r"D:\\dexa\\input_data")

    # Recursively find all .txt files in all subfolders
    txt_files = list(input_dir.rglob("*.txt")) + list(input_dir.rglob("*.TXT"))

    if not txt_files:
        print(f"⚠️ No TXT files found in directory: {input_dir}")
    else:
        for txt_file in txt_files:
            # Find matching .xml file in the same directory
            xml_candidates = list(txt_file.parent.glob("*.xml")) + list(txt_file.parent.glob("*.XML"))

            if not xml_candidates:
                print(f"❌ No XML file found for {txt_file}")
                continue

            xml_file = xml_candidates[0]

            try:
                print(f"🔄 Processing: {txt_file.name}")
                process_file_pair(txt_file, xml_file)
                print(f"✅ Done: {txt_file.name}")
            except Exception as e:
                print(f"❌ Failed to process {txt_file.name}: {e}")
    