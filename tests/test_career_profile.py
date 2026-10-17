from app.models.career_profile import CareerProfile


def main():

    profile_data = {

        "profession":"Technology",

        "role":"Backend Engineer",

        "industry":"Software",

        "seniority":"Junior",

        "competencies":{

            "technical":[
                "Python",
                "FastAPI"
            ],

            "tools":[
                "Git"
            ]

        }

    }


    profile = CareerProfile.from_dict(profile_data)


    print(profile.to_dict())



if __name__ == "__main__":

    main()