import json


def transform_line(line, processed):
    try:
        data = json.loads(line.strip())

        actor_id = data.get("actorID", "")
        action = data.get("action", "")
        object_id = data.get("objectID", "")

        new_data = {"subject": actor_id, "event": action, "object": object_id}

        if (actor_id, action, object_id) in processed:
            return None
        processed.add((actor_id, action, object_id))

        return json.dumps(new_data)

    except json.JSONDecodeError:
        print(f"Failed to parse JSON line: {line}")
        return None


def process_file(input_file, output_file):
    processed = set()
    with open(input_file, "r", encoding="utf-8") as infile, open(
        output_file, "w", encoding="utf-8"
    ) as outfile:

        for line in infile:
            transformed_line = transform_line(line, processed)
            if transformed_line:
                outfile.write(transformed_line + "\n")


def parse(input_filename, output_filename):
    process_file(input_filename, output_filename)


if __name__ == "__main__":
    input_filename = "SysClient0201.systemia.com.txt"
    output_filename = "optc-201.jsonl"

    parse(input_filename, output_filename)
