
class TimetableGenerator:

    def __init__(self, faculty_records, working_days=None):

        self.faculty_records = faculty_records

        self.working_days = working_days or [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday"
        ]

        self.time_slots = [
            "10:00 AM - 11:00 AM",
            "11:00 AM - 12:00 PM",
            "12:00 PM - 1:00 PM",
            "2:00 PM - 3:00 PM",
            "3:00 PM - 4:00 PM",
            "4:00 PM - 5:00 PM"
        ]

    def generate_timetable(self):

        timetable = {}
        faculty_busy = set()
        class_busy = set()

        faculty_day_count = {}
        class_day_count = {}

        for record in self.faculty_records:

            class_name = (
                f"{record['branch']} - Semester {record['semester']}"
            )

            if class_name not in timetable:

                timetable[class_name] = {}

                for day in self.working_days:

                    timetable[class_name][day] = []

                    for period, time in enumerate(self.time_slots, 1):

                        timetable[class_name][day].append({
                            "lecture": period,
                            "time": time,
                            "subject": "Free",
                            "faculty_name": "",
                            "faculty_id": ""
                        })

        records = sorted(
            self.faculty_records,
            key=lambda item: int(item["weekly_lectures"]),
            reverse=True
        )

        for record in records:

            faculty_id = record["faculty_id"]
            faculty_name = record["faculty_name"]
            branch = record["branch"]
            semester = record["semester"]
            subject = record["subject"]

            weekly_lectures = int(record["weekly_lectures"])

            class_name = f"{branch} - Semester {semester}"

            if not 1 <= weekly_lectures <= 40:
                raise ValueError(
                    f"Invalid lecture count for {faculty_name}"
                )

            for _ in range(weekly_lectures):

                available_slots = []

                for day_index, day in enumerate(self.working_days):

                    for period in range(1, 7):

                        teacher_slot = (faculty_id, day, period)
                        class_slot = (class_name, day, period)

                        if teacher_slot in faculty_busy:
                            continue

                        if class_slot in class_busy:
                            continue

                        teacher_load = faculty_day_count.get(
                            (faculty_id, day), 0
                        )

                        class_load = class_day_count.get(
                            (class_name, day), 0
                        )

                        available_slots.append((
                            teacher_load,
                            class_load,
                            day_index,
                            period,
                            day
                        ))

                if not available_slots:
                    raise ValueError(
                        f"Not enough available slots for {faculty_name}"
                    )

                available_slots.sort()

                _, _, _, period, day = available_slots[0]

                faculty_busy.add((faculty_id, day, period))
                class_busy.add((class_name, day, period))

                faculty_day_count[(faculty_id, day)] = (
                    faculty_day_count.get((faculty_id, day), 0) + 1
                )

                class_day_count[(class_name, day)] = (
                    class_day_count.get((class_name, day), 0) + 1
                )

                timetable[class_name][day][period - 1] = {
                    "lecture": period,
                    "time": self.time_slots[period - 1],
                    "subject": subject,
                    "faculty_name": faculty_name,
                    "faculty_id": faculty_id
                }

        return timetable
