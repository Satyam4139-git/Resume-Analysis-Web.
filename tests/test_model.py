from app.services.ai_service import AIService


def main():

    print("\nStarting AI Model Test...\n")


    ai_service = AIService()


    response = ai_service.send_prompt(
        """
        Reply only with:
        AI Model is working successfully.
        """
    )


    print("=" * 60)
    print("AI RESPONSE")
    print("=" * 60)

    print(response)

    print("=" * 60)



if __name__ == "__main__":
    main()