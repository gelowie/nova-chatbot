// Time skill: clock, dates and calendar offsets
package nova;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.format.TextStyle;
import java.util.Arrays;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class TimeReader {

    public static final ZoneId ZONE = ZoneId.systemDefault();
    public static final Locale LOCALE = Locale.ENGLISH;
    public static final int MAX_OFFSET = 10_000;

    private static final DateTimeFormatter PRETTY =
        DateTimeFormatter.ofPattern("EEEE, dd MMMM yyyy", LOCALE);
    private static final DateTimeFormatter CLOCK =
        DateTimeFormatter.ofPattern("HH:mm", LOCALE);
    private static final DateTimeFormatter FULL_CLOCK =
        DateTimeFormatter.ofPattern("HH:mm:ss", LOCALE);

    // Detection rules, one-to-one with src/py/time_reader.py
    private static final Pattern REL = Pattern.compile(
        "\\b(\\d+)\\s*(days?|weeks?|months?)\\b", Pattern.CASE_INSENSITIVE);
    private static final Pattern REL_CUE = Pattern.compile(
        "\\b(?:in|after|add)\\s+\\d+\\s*(?:days?|weeks?|months?)\\b"
        + "|\\bdate\\b|\\bfrom (?:now|today)\\b");
    private static final Pattern TIME_Q = Pattern.compile(
        "\\b(?:what time|current time|time now|time please|clock"
        + "|(?:what(?:'s| is)?|whats|tell me|know|got|have|give me|check) the time)\\b"
        + "|^\\W*time\\W*$");
    private static final Pattern DATE_Q = Pattern.compile(
        "\\bdate\\b|\\b(?:what is|what's|whats) today\\b|^\\W*today\\W*$");
    private static final Pattern WEEKDAY_Q = Pattern.compile(
        "\\b(?:what day|which day|day of the week|name of the day)\\b");
    private static final Pattern NEXT_MONTH_Q = Pattern.compile(
        "\\b(?:next month|following month|a month from now)\\b");
    private static final Pattern LAST_MONTH_Q = Pattern.compile(
        "\\b(?:last month|previous month|a month ago)\\b");

    // Tomorrow and yesterday need a cue
    private static final String DAY_CUE =
        "(?:what(?:'s| is| was| will)?|whats|which|tell me|give me)\\s+"
        + "(?:the\\s+)?(?:date\\s+|day\\s+)?(?:is\\s+|was\\s+|of\\s+|for\\s+)?(?:it\\s+)?";

    private static Pattern dayQuestion(String word) {
        return Pattern.compile(
            "^\\W*" + word + "\\W*$"
            + "|\\b" + DAY_CUE + word + "\\b"
            + "|\\b" + word + "'?s?\\s+(?:date|day)\\b"
            + "|\\bdate\\s+(?:of|for)\\s+" + word + "\\b");
    }

    private static final Pattern TOMORROW_Q = dayQuestion("tomorrow");
    private static final Pattern YESTERDAY_Q = dayQuestion("yesterday");

    private TimeReader() {}

    // Clock readings
    public static LocalDate today() {
        return LocalDate.now(ZONE);
    }

    public static LocalTime now() {
        return LocalTime.now(ZONE);
    }

    public static String clock() {
        return now().format(CLOCK);
    }

    public static String dayName() {
        return today().getDayOfWeek().getDisplayName(TextStyle.FULL, LOCALE);
    }

    public static String pretty(LocalDate date) {
        return date.format(PRETTY);
    }

    // Calendar arithmetic
    public static LocalDate nextMonth() {
        return today().plusMonths(1);
    }

    public static LocalDate prevMonth() {
        return today().minusMonths(1);
    }

    public static LocalDate shift(int days, int weeks, int months) {
        return today().plusDays(days).plusWeeks(weeks).plusMonths(months);
    }

    // Public entry point
    public static String handle(String raw) {
        if (raw == null || raw.isBlank()) return null;
        String q = raw.toLowerCase(LOCALE).strip();

        // Relative offsets ("date in 3 weeks")
        Matcher offset = REL.matcher(q);
        if (offset.find() && REL_CUE.matcher(q).find()) {
            String digits = offset.group(1).replaceFirst("^0+(?!$)", "");
            if (digits.length() > 6 || Integer.parseInt(digits) > MAX_OFFSET) {
                return "That's too far away for me to work out reliably — try "
                     + String.format("%,d", MAX_OFFSET) + " or fewer.";
            }
            int amount = Integer.parseInt(digits);
            String unit = offset.group(2).toLowerCase(LOCALE);
            LocalDate target = unit.startsWith("week")  ? shift(0, amount, 0)
                             : unit.startsWith("month") ? shift(0, 0, amount)
                             :                            shift(amount, 0, 0);
            return "That lands on **" + pretty(target) + "** (" + target + ").";
        }

        if (containsAny(q, "date and time", "full date", "timestamp")) {
            return "It's **" + pretty(today()) + " at "
                 + now().format(FULL_CLOCK) + "** right now.";
        }

        // Before the weekday check
        if (TOMORROW_Q.matcher(q).find()) {
            return "Tomorrow is **" + pretty(shift(1, 0, 0)) + "**.";
        }
        if (YESTERDAY_Q.matcher(q).find()) {
            return "Yesterday was **" + pretty(shift(-1, 0, 0)) + "**.";
        }

        if (WEEKDAY_Q.matcher(q).find()) {
            return "Today is **" + dayName() + "** — " + pretty(today())
                 + " (" + today() + ").";
        }

        if (NEXT_MONTH_Q.matcher(q).find()) {
            LocalDate target = nextMonth();
            return "One month from today will be **" + pretty(target) + "** (" + target + ").";
        }
        if (LAST_MONTH_Q.matcher(q).find()) {
            LocalDate target = prevMonth();
            return "One month before today was **" + pretty(target) + "** (" + target + ").";
        }

        if (TIME_Q.matcher(q).find()) {
            return "It's **" + clock() + "** on your system clock.";
        }

        // Broadest check, so it goes last
        if (DATE_Q.matcher(q).find()) {
            return "Today is **" + pretty(today()) + "** (" + today() + ").";
        }

        return null;
    }

    private static boolean containsAny(String haystack, String... needles) {
        return Arrays.stream(needles).anyMatch(haystack::contains);
    }

    // Self-test
    public static void main(String[] args) {
        String[] prompts = {
            "what time is it",
            "what day is it today",
            "what is the date",
            "what is the date next month",
            "what was the date last month",
            "what will the date be in 3 weeks",
            "date in 5 days",
            "what is tomorrow",
            "what was yesterday",
            "full date and time please",
            "tell me a joke",
            "whats 5 plus 3"
        };
        for (String prompt : prompts) {
            System.out.printf("%-42s → %s%n", prompt, handle(prompt));
        }

        System.out.println();
        System.out.println("Edge case: 31 Jan 2026 + 1 month = "
            + LocalDate.of(2026, 1, 31).plusMonths(1));
        System.out.println("Edge case: 31 Jan 2024 + 1 month = "
            + LocalDate.of(2024, 1, 31).plusMonths(1) + "  (leap year)");
    }
}
