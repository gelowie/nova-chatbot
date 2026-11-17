// Math skill: arithmetic from words or symbols
package nova;

import java.math.BigDecimal;
import java.math.MathContext;
import java.util.List;
import java.util.regex.Pattern;

public final class MathSolver {
    private static final String DIV_BY_ZERO = "I can't divide by zero — that one breaks the universe.";

    private record WordOp(Pattern pattern, String symbol) {
        WordOp(String regex, String symbol) {
            this(Pattern.compile(regex), symbol);
        }
    }

    // Word operators (order matters)
    private static final List<WordOp> WORD_OPS = List.of(
        new WordOp("to the power of", "^"),
        new WordOp("multiplied by",   "*"),
        new WordOp("multiply by",     "*"),
        new WordOp("divided by",      "/"),
        new WordOp("divide by",       "/"),
        new WordOp("take away",       "-"),
        new WordOp("added to",        "+"),
        new WordOp("\\s*squared",     "^2"),
        new WordOp("\\s*cubed",       "^3"),
        new WordOp("\\bplus\\b",      "+"),
        new WordOp("\\bminus\\b",     "-"),
        new WordOp("\\btimes\\b",     "*"),
        new WordOp("\\bover\\b",      "/"),
        new WordOp("\\bmodulo\\b",    "%"),
        new WordOp("\\bmod\\b",       "%"),
        new WordOp("\\bpower\\b",     "^"),
        new WordOp("\\bpercent\\b",   "%")
    );

    private static final Pattern FILLERS = Pattern.compile(
        "^\\s*(?:hey|hi|hello|nova|please|pls|" +
        "can you|could you|would you|" +
        "what(?:'s| is)?|whats|" +
        "how much is|how many is|how much|" +
        "calculate|compute|solve|evaluate|work out|" +
        "tell me|give me|show me|answer|equals?)\\s+",
        Pattern.CASE_INSENSITIVE);

    private static final Pattern HAS_DIGIT = Pattern.compile("\\d");
    private static final Pattern HAS_OPERATOR = Pattern.compile("[+\\-*/%^]");
    private static final Pattern ALLOWED = Pattern.compile("^[\\d+\\-*/%^().\\s]+$");

    private MathSolver() {}

    // Public entry point
    public static String solve(String raw) {
        String expr = normalize(raw);
        if (expr == null) return null;

        double value;
        try {
            value = new Parser(expr).parse();
        } catch (ArithmeticException e) {
            return DIV_BY_ZERO;
        } catch (IllegalArgumentException e) {
            return null;
        }
        if (Double.isInfinite(value)) return DIV_BY_ZERO;
        if (Double.isNaN(value)) return null;

        String pretty = expr.replace("*", " × ")
                            .replace("/", " ÷ ")
                            .replaceAll("\\s+", " ")
                            .trim();
        return "Solved **" + pretty + "** = **" + fmt(value) + "**";
    }

    // Prompt to expression
    static String normalize(String raw) {
        if (raw == null) return null;

        String expr = raw.toLowerCase().trim()
                         .replace(",", "")
                         .replace("÷", "/")
                         .replace("×", "*")
                         .replaceAll("[?!=]", " ");

        // Leading filler
        for (int pass = 0; pass < 6; pass++) {
            String stripped = FILLERS.matcher(expr).replaceFirst("");
            if (stripped.equals(expr)) break;
            expr = stripped;
        }

        expr = expr.replaceAll("(\\d+(?:\\.\\d+)?)\\s*(?:%|percent)\\s*of\\s*", "($1/100)*");
        expr = expr.replaceAll("(?<=\\d)\\s*x\\s*(?=\\d)", "*");

        for (WordOp op : WORD_OPS) {
            expr = op.pattern().matcher(expr).replaceAll(op.symbol());
        }

        expr = expr.replaceAll("\\s+", " ").trim()
                   .replaceAll("[+*/^]+$", "").trim();

        // Validation gates
        boolean looksLikeMath = HAS_DIGIT.matcher(expr).find()
                && HAS_OPERATOR.matcher(expr).find()
                && ALLOWED.matcher(expr).matches();
        return looksLikeMath ? expr : null;
    }

    // Number formatting; doubles, so whole results past 2^53 can differ from Python
    private static String fmt(double value) {
        if (value == Math.rint(value)) {
            return new BigDecimal(value).toBigInteger().toString();
        }
        return new BigDecimal(value).round(new MathContext(10))
                                    .stripTrailingZeros().toPlainString();
    }

    // Recursive-descent parser
    private static final class Parser {
        private final String src;
        private int pos;

        Parser(String src) {
            this.src = src;
        }

        double parse() {
            double result = expr();
            if (peek() != '\0') {
                throw new IllegalArgumentException("unexpected '" + src.charAt(pos) + "'");
            }
            return result;
        }

        private char peek() {
            while (pos < src.length() && Character.isWhitespace(src.charAt(pos))) pos++;
            return pos < src.length() ? src.charAt(pos) : '\0';
        }

        private double expr() {
            double acc = term();
            while (peek() == '+' || peek() == '-') {
                char op = src.charAt(pos++);
                double rhs = term();
                acc = op == '+' ? acc + rhs : acc - rhs;
            }
            return acc;
        }

        private double term() {
            double acc = unary();
            while (peek() == '*' || peek() == '/' || peek() == '%') {
                char op = src.charAt(pos++);
                double rhs = unary();
                if ((op == '/' || op == '%') && rhs == 0) {
                    throw new ArithmeticException("division by zero");
                }
                // Modulo takes the divisor's sign, like Python
                switch (op) {
                    case '*' -> acc *= rhs;
                    case '/' -> acc /= rhs;
                    default -> acc = ((acc % rhs) + rhs) % rhs;
                }
            }
            return acc;
        }

        private double unary() {
            char sign = peek();
            if (sign != '+' && sign != '-') return power();

            pos++;
            double operand = unary();
            return sign == '-' ? -operand : operand;
        }

        private double power() {
            double base = primary();
            if (peek() != '^') return base;

            pos++;
            double exp = unary();
            if (Math.abs(exp) > 64) {
                throw new IllegalArgumentException("exponent too large");
            }
            return Math.pow(base, exp);
        }

        private double primary() {
            if (peek() == '(') {
                pos++;
                double inner = expr();
                if (peek() != ')') throw new IllegalArgumentException("missing ')'");
                pos++;
                return inner;
            }

            int start = pos;
            while (pos < src.length()
                   && (Character.isDigit(src.charAt(pos)) || src.charAt(pos) == '.')) {
                pos++;
            }
            if (start == pos) throw new IllegalArgumentException("expected number");
            return Double.parseDouble(src.substring(start, pos));
        }
    }

    // Self-test
    public static void main(String[] args) {
        String[] prompts = {
            "whats 5 plus 3 times 2",
            "hey can you calculate 144 divided by 12",
            "15% of 200",
            "2^10",
            "100 / 0",
            "(12 + 8) / 4",
            "-5 + 10",
            "5 x 3",
            "3 squared plus 4 squared",
            "20 modulo 7",
            "hello",
            "tell me a joke",
            "5",
            "what time is it"
        };
        for (String prompt : prompts) {
            System.out.printf("%-42s → %s%n", prompt, solve(prompt));
        }
    }
}
