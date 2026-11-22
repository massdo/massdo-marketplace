# The Nestor antipatterns are declared once, in the skill body

The body of a skill is what a client injects into the conversation. The frontmatter keeps the portable Agent Skills fields only. The antipatterns of the `nestor` skill are the bullets of the `## antipattern` section of its body, and nowhere else.

Validation requires that section and each expected antipattern in it.

Code:

- `scripts/validate.py`: the `nestor` branch of the namesake skill checks
