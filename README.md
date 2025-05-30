# egglog-latex

convert egglog rewrite rules to LaTeX mathematical notation.

## Usage

Convert an egglog rule to LaTeX format:

```python
from egglog_to_inference import convert_rule
from IPython.display import display, Math

# Convert the rule to LaTeX
result = convert_rule(eg2)
print(eg2)

# Display the formatted equation
display(Math(result))
```

## Example Rule

```lisp
rewrite(pow(x, Lit64(ival))).to(
    mul(x, pow(x, Lit64(ival - 1))),
    ival >= 1,
)
```

## Formal Representation

$$
\frac{expr = pow(x, Lit64(ival)), ival \geq 1}{expr \to mul(x, pow(x, Lit64(ival - 1)))}
$$
