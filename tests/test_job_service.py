from app.services.job_service import JobService


def main():

    service = JobService()

    result = service.get_target_job(
        "Google",
        "Backend Engineer"
    )

    print(result)


if __name__ == "__main__":
    main()