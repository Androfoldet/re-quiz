def get_winner(scores):
    return max(scores, key=scores.get)


def build_result_text(character):
    return (
        f"🧟 *ТВОЙ ПЕРСОНАЖ — {character['name'].upper()}*\n\n"
        f"_{character['quote']}_\n\n"
        f"📖 {character['description']}\n\n"
        f"🎯 *Почему ты — это {character['name']}:*\n"
        f"{character['why']}"
    )
