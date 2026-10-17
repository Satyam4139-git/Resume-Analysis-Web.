from app.services.job_service import JobService


def main():

    service = JobService()

    job = service.get_target_job(

        "Google",

        "Backend Engineer"

    )

    print(job.title)

    print(job.company.name)

    print(job.competencies)


if __name__ == "__main__":

    main()