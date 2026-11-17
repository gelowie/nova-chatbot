// Router: local skills first, the JSON brain takes the rest
package nova;

public final class NovaEngine {

    public record Reply(String text, String skill) {
        public Reply {
            if (text == null) throw new IllegalArgumentException("text is null");
            if (skill == null) skill = "unknown";
        }
    }

    private NovaEngine() {}

    public static Reply respond(String message) {
        if (message == null || message.isBlank()) return null;

        // Math goes first: "5 + 5" could otherwise read as chat
        String math = MathSolver.solve(message);
        if (math != null) return new Reply(math, "math");

        String time = TimeReader.handle(message);
        if (time != null) return new Reply(time, "time");

        // Nothing local matched; the caller tries the JSON brain
        return null;
    }

    // Routing demo
    public static void main(String[] args) {
        String[] prompts = {
            // Math
            "whats 5 plus 3 times 2",
            "can you calculate 144 divided by 12",
            "15% of 200",
            "2^10",
            "(12 + 8) / 4",
            "3 squared plus 4 squared",
            "100 / 0",
            // Time
            "what time is it",
            "what day is it today",
            "what is the date",
            "what is the date next month",
            "what was the date last month",
            "what will the date be in 3 weeks",
            "what is tomorrow",
            "full date and time please",
            // Falls through to the brain
            "tell me a joke",
            "hello there",
            "i am bored",
            "asdfghjkl"
        };

        System.out.println("┌─────────────────────────────────────────────────────────────────────┐");
        System.out.println("│  Nova Java engine — routing demonstration                           │");
        System.out.println("└─────────────────────────────────────────────────────────────────────┘");
        System.out.println();

        int mathCount = 0, timeCount = 0, deferCount = 0;
        for (String prompt : prompts) {
            Reply reply = respond(prompt);

            String skill = "defer";
            String preview = "(falls through to JSON brain)";
            if (reply == null) {
                deferCount++;
            } else {
                skill = reply.skill();
                String[] lines = reply.text().split("\n", 2);
                preview = lines.length > 1 ? lines[0] + " …" : lines[0];
                switch (skill) {
                    case "math" -> mathCount++;
                    case "time" -> timeCount++;
                    default -> { }
                }
            }
            System.out.printf("  [%-5s]  %-38s → %s%n", skill, prompt, preview);
        }

        System.out.println();
        System.out.println("Summary:");
        System.out.printf("  math   → %d%n", mathCount);
        System.out.printf("  time   → %d%n", timeCount);
        System.out.printf("  defer  → %d   (would go to JSON brain)%n", deferCount);
        System.out.println();

        // End-of-month clamping
        System.out.println("Edge case — end-of-month clamping (handled by java.time):");
        System.out.println("  31 Jan 2026 + 1 month = "
            + java.time.LocalDate.of(2026, 1, 31).plusMonths(1));
        System.out.println("  31 Jan 2024 + 1 month = "
            + java.time.LocalDate.of(2024, 1, 31).plusMonths(1) + "  (leap year)");
        System.out.println("  31 Aug 2026 + 1 month = "
            + java.time.LocalDate.of(2026, 8, 31).plusMonths(1));
    }
}
