The MyDoctor application aims to be a management tool for the appointments of a doctor.
A hospital has multiple offices.
The users of the application can be doctors and patients.
The doctors can apply to practice in offices and create a schedule for an office. The schedules in different offices can’t overlay.
📝 Example:
Doctor Ana is available in Office 4 on the 4th of September during 1 PM - 5PM. Doctor Ana can’t practice in Office 5 on the 4th of September during 3PM - 8 PM, but she can practice in Office 5 on the 4th of September during 5:30PM - 8 PM.
The patients can see the existing doctors in the system, the schedule of the offices and can book appointments for specific doctors and for specific schedules. The appointments can be of 3 types:
- Blood Test - 15 mins
- Consultation - 30 mins
- Surgery - 60 mins
The booking of an appointment will not be possible if another appointment is already booked at the same time frame. An email is sent to the patient with the confirmation of the appointment.
📝 Example:
Action 1: User Mike will create a blood test booking for Doctor Ana for the 4th of September starting with 15:30 PM → Possible
Action 2: User Mike will create an intervention booking for Doctor Ana for the 4th of September starting with 15:00 PM → Not Possible
Action 3: User Mike will create an intervention booking for Doctor Ana for the 4th of September starting with 16:00 PM → Possible
