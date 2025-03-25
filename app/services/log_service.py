import re
from sqlalchemy.orm import Session
from datetime import datetime
from message_templates import MESSAGE_TEMPLATES
from app.models.log import LogEntry

VAR_PLACEHOLDERS = ['&A', '&B', '&C', '&D', '&E', '&F', '&G', '&H', '&I', '&J']


class LogParser:
    def __init__(self, file_path, db_session=None, sap_system_id=None, app_server_instance=None, file_checker_id=None,
                 delimiter=None):
        self.file_path = file_path
        self.db = db_session
        self.sap_system_id = sap_system_id
        self.app_server_instance = app_server_instance
        self.file_checker_id = file_checker_id
        self.delimiter = delimiter

    def parse_and_store(self):
        try:
            parsed_segments = self._process_audit_file()
            parsed_logs = self._parse_log_data(parsed_segments)

            if self.db:
                self._save_parsed_logs(parsed_logs)

            return True
        except Exception as e:
            print(f"Error in parse_and_store: {str(e)}")
            return False

    def _process_audit_file(self):
        print(f"Processing file: {self.file_path}")
        print(f"Original delimiter: {self.delimiter}")

        with open(self.file_path, "r") as f:
            content = f.read()
        print(f"Original file content length: {len(content)}")
        # stripped_content = content[101:] if len(content) >= 101 else ""
        print(f"Content length after stripping: {len(content)}")
        message_classes = list(MESSAGE_TEMPLATES.keys())
        if not message_classes:
            raise ValueError("No message classes found in MESSAGE_TEMPLATES")
        delimiter_escaped = re.escape(self.delimiter)
        message_class_pattern = '|'.join(re.escape(cls) for cls in message_classes)
        replacement_pattern = re.compile(f"({delimiter_escaped})({message_class_pattern})")
        modified_content = replacement_pattern.sub(rf"\1TRNT\2", content)
        print(f"Modified content length after replacement: {len(modified_content)}")

        new_delimiter = self.delimiter + "TRNT"
        print(f"New delimiter for splitting: {new_delimiter}")
        delimiter_pattern = re.compile(re.escape(new_delimiter))
        parsed_segments = delimiter_pattern.split(modified_content)

        print(f"Number of valid parsed segments: {len(parsed_segments)}")

        return parsed_segments

    def _parse_log_data(self, parsed_segments):
        parsed_logs = []

        for data in parsed_segments:


            message_id = data[:3]
            if message_id not in MESSAGE_TEMPLATES:
                print(f"Skipping segment with unknown message ID '{message_id}'")
                continue

            log_entry = self._create_base_log_entry(data)

            index = 35
            var_fields = [
                "short_terminal_name", "user", "transaction_code",
                "program", "long_terminal_name", "last_address_routed_no_of_variables"
            ]

            for field in var_fields:
                log_entry[field], index = self._extract_field(data, index)
            variables, _ = self._extract_event_data(data, index)
            self._add_variables_to_log(log_entry, variables)
            self._apply_message_template(log_entry)

            parsed_logs.append(log_entry)

        return parsed_logs

    def _create_base_log_entry(self, data):
        message_id = data[:3]
        raw_date = data[3:11]
        raw_time = data[11:17]

        formatted_date, formatted_time = self._format_date_time(raw_date, raw_time)

        return {
            "sap_system_id": self.sap_system_id,
            "app_server_instance": self.app_server_instance,
            "message_identifier": message_id,
            "syslog_msg_group": data[:2],
            "sub_name": data[2:3],
            "date": formatted_date,
            "time": formatted_time,
            "operating_system_number": data[19:24],
            "work_process_number": data[24:29],
            "sap_process": data[29:31],
            "client": data[31:34],
            "file_number": data[34:35],
            "short_terminal_name": "",
            "user": "",
            "transaction_code": "",
            "program": "",
            "long_terminal_name": "",
            "last_address_routed_no_of_variables": "",
            "first_variable_value": "",
            "second_variable_value": "",
            "third_variable_value": "",
            "other_variable_values": "",
            "audit_log_msg_text": "",
            "audit_class": "",
            "message_severity": "",
            "criticality": "M",
            "all_variables": []
        }

    def _extract_field(self, data, start_idx):
        try:
            field_length_str = data[start_idx:start_idx + 4]
            if not field_length_str.isdigit():
                print(f"Invalid field length at position {start_idx}: '{field_length_str}'")
                return "", start_idx + 4

            field_length = int(field_length_str)

            if start_idx + 4 + field_length > len(data):
                print(f"Field length {field_length} exceeds available data at position {start_idx}")
                return "", start_idx + 4

            field_value = data[start_idx + 4:start_idx + 4 + field_length]
            return field_value, start_idx + 4 + field_length
        except Exception as e:
            print(f"Error extracting field at {start_idx}: {e}")
            return "", start_idx + 4

    def _extract_event_data(self, data, start_idx):
        try:
            length_str = data[start_idx:start_idx + 4]
            if not length_str.isdigit():
                print(f"Invalid event data length at position {start_idx}: '{length_str}'")
                return [], start_idx + 4

            length = int(length_str)
            end_idx = start_idx + 4 + length

            if end_idx > len(data):
                print(f"Event data length {length} exceeds available data at position {start_idx}")
                return [], start_idx + 4

            event_data = data[start_idx + 4:end_idx]
            variables = event_data.split('&') if event_data else []
            return variables, end_idx
        except Exception as e:
            print(f"Error extracting event data at {start_idx}: {e}")
            return [], start_idx + 4

    def _add_variables_to_log(self, log_entry, variables):
        log_entry["all_variables"] = variables

        if variables:
            log_entry["first_variable_value"] = variables[0] if len(variables) > 0 else ""
            log_entry["second_variable_value"] = variables[1] if len(variables) > 1 else ""
            log_entry["third_variable_value"] = variables[2] if len(variables) > 2 else ""
            log_entry["other_variable_values"] = "&".join(variables[3:]) if len(variables) > 3 else ""

    def _apply_message_template(self, log_entry):
        message_id = log_entry["message_identifier"]
        template = MESSAGE_TEMPLATES.get(message_id)

        if template:
            message = template["message_text"]
            for i, var in enumerate(log_entry["all_variables"]):
                if i < len(VAR_PLACEHOLDERS):
                    message = message.replace(VAR_PLACEHOLDERS[i], var)

            log_entry.update({
                "audit_log_msg_text": message,
                "audit_class": template["audit_class"],
                "message_severity": template["message_severity"],
                "criticality": "H" if template["message_severity"] == "High"
                else "M" if template["message_severity"] == "Medium"
                else "L"
            })

    def _save_parsed_logs(self, parsed_logs):
        for entry in parsed_logs:
            if "all_variables" in entry:
                entry.pop("all_variables")
            new_log = LogEntry(**entry)
            self.db.add(new_log)
        self.db.commit()

    @staticmethod
    def _format_date_time(raw_date, raw_time):
        formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        time_obj = datetime.strptime(raw_time, "%H%M%S")
        formatted_time = time_obj.strftime("%I:%M:%S %p")
        return formatted_date, formatted_time


def parse_and_store_logs(file_path: str, db: Session, sap_system_id=None, app_server_instance=None,
                         file_checker_id=None, delimiter=None):
    try:
        parser = LogParser(
            file_path=file_path,
            db_session=db,
            sap_system_id=sap_system_id,
            app_server_instance=app_server_instance,
            file_checker_id=file_checker_id,
            delimiter=delimiter
        )
        return parser.parse_and_store()
    except Exception as e:
        print(f"Error parsing logs: {str(e)}")
        return False