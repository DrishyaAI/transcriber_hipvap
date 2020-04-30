import mmap
from itertools import islice
from struct import Struct

from transcriber.converter.workers import utils
from transcriber.dbf.parser import Parser


def write_csv(csv_file, csv_data):
    csv_file.write("".join(csv_data))


class CSVWorker:
    def __init__(self, filename, tags, tag_lookup):
        self.filename = filename
        self.tags = tags
        self.tag_lookup = tag_lookup
        self.number_of_tags = len(self.tag_lookup)

    def work(self):
        self.convert()
        return self.filename

    def convert(self):
        with open(self.filename) as _input_csv:
            input_csv = mmap.mmap(
                _input_csv.fileno(), 0, access=mmap.ACCESS_READ
            )

            with open(
                utils.transcribed_filename(self.filename), "w"
            ) as csv_file:
                write_csv(csv_file, self.generate_csv(input_csv))

    def generate_csv(self, input_csv):
        lines = sorted([self.tag_lookup.index(t) for t in self.tags])
        lines_set = set(lines)
        number_of_tags = self.number_of_tags

        yield ",".join(["Date", "Time", *[self.tag_lookup[i] for i in lines]])

        tags_written = num_tags = len(lines)
        for i, line in enumerate(islice(input_csv, 1, None)):
            if i % number_of_tags not in lines_set:
                continue
            if tags_written == num_tags:
                date, time, _, val = utils.data_from_line(line)
                yield f"\n{date},{time},{val}"
                tags_written = 1
            else:
                yield f",{utils.val_from_line(line)}"
                tags_written += 1


class DBFWorker(CSVWorker):
    def __init__(self, filename, tags, tag_lookup):
        super(DBFWorker, self).__init__(filename, tags, tag_lookup)
        self.parser = Parser(
            required_fields=["Date", "Time", "Value"],
            required_tags=[self.tag_lookup.index(t) for t in self.tags],
            all_tags=tag_lookup,
        )

    def convert(self):
        table = self.parser.parse_selection(self.filename)
        with open(utils.transcribed_filename(self.filename), "w") as csv_file:
            write_csv(csv_file, self.generate_csv(table))

    def generate_csv(self, table):
        lines = sorted([self.tag_lookup.index(t) for t in self.tags])
        double_struct = Struct("<d")
        unpack = double_struct.unpack

        yield ",".join(["Date", "Time", *[self.tag_lookup[l] for l in lines]])

        tags_written = num_tags = len(lines)
        for row in table:
            value = round(unpack(row["Value"])[0], 8)
            if tags_written == num_tags:
                date = utils.format_dbf_date(row["Date"].decode())
                time = row["Time"].decode()
                yield f"\n{date},{time},{value}"
                tags_written = 1
            else:
                yield f",{value}"
                tags_written += 1
