# Processors

The true power of *structlog* lies in its *combinable log processors*.
A log processor is a regular callable or in other words:
A function or an instance of a class with a `__call__()` method.

(chains)=

## Chains

The *processor chain* is a list of processors.
Each processors receives three positional arguments:

**logger**

: Your wrapped logger object that is called with the final processor return value.
  For example {class}`logging.Logger` or {class}`structlog.PrintLogger` (default).

**method_name**

: The name of the wrapped method.
  If you called `log.warning("foo")`, it will be `"warning"`.

**event_dict**

: Current context together with the current event.
  If the context was `{"a": 42}` and the event is `"foo"`, the initial `event_dict` will be `{"a":42, "event": "foo"}`.

The return value of each processor is passed on to the next one as `event_dict` until finally the return value of the last processor gets passed into the wrapped logging method.

:::{note}
*structlog* only looks at the return value of the **last** processor.
That means that as long as you control the next processor in the chain (the processor that will get your return value passed as an argument), you can return whatever you want.

Returning a modified event dictionary from your processors is just a convention to make processors composable.
:::


### Examples

If you set up your logger like:

```python
structlog.configure(processors=[f1, f2, f3])
log = structlog.get_logger().bind(x=42)
```

and call `log.info("some_event", y=23)`, it results in the following call chain:

```python
wrapped_logger.info(
   f3(wrapped_logger, "info",
      f2(wrapped_logger, "info",
         f1(wrapped_logger, "info", {"event": "some_event", "x": 42, "y": 23})
      )
   )
)
```

In this case, `f3` has to make sure it returns something `wrapped_logger.info` can handle (see {ref}`adapting`).
For the example with `PrintLogger` above, this means `f3` must return a string.

The simplest modification a processor can make is adding new values to the `event_dict`.
Parsing human-readable timestamps is tedious, not so [UNIX timestamps](https://en.wikipedia.org/wiki/UNIX_time) -- let's add one to each log entry:

```python
import calendar
import time

def timestamper(logger, log_method, event_dict):
    event_dict["timestamp"] = calendar.timegm(time.gmtime())
    return event_dict
```

:::{important}
You're explicitly allowed to modify the `event_dict` parameter, because a copy has been created before calling the first processor.
:::

Please note that *structlog* comes with such a processor built in: {class}`~structlog.processors.TimeStamper`.


## Filtering

If a processor raises {class}`structlog.DropEvent`, the event is silently dropped.

Therefore, the following processor drops every entry:

```python
from structlog import DropEvent

def dropper(logger, method_name, event_dict):
    raise DropEvent
```

But we can do better than that!

(cond-drop)=

How about dropping only log entries that are marked as coming from a certain peer (for example, monitoring)?

```python
class ConditionalDropper:
    def __init__(self, peer_to_ignore):
        self._peer_to_ignore = peer_to_ignore

    def __call__(self, logger, method_name, event_dict):
        """
        >>> cd = ConditionalDropper("127.0.0.1")
        >>> cd(None, "", {"event": "foo", "peer": "10.0.0.1"})
        {'peer': '10.0.0.1', 'event': 'foo'}
        >>> cd(None, "", {"event": "foo", "peer": "127.0.0.1"})
        Traceback (most recent call last):
        ...
        DropEvent
        """
        if event_dict.get("peer") == self._peer_to_ignore:
            raise DropEvent

        return event_dict
```

Since it's so common to filter by the log level, *structlog* comes with {func}`structlog.make_filtering_bound_logger` that filters log entries before they even enter the processor chain.
It does **not** use the standard library, but it does use its names and order of log levels.

(adapting)=

## Adapting and rendering

An important role is played by the *last* processor because its duty is to adapt the `event_dict` into something the logging methods of the *wrapped logger* understand.
With that, it's also the *only* processor that needs to know anything about the underlying system.

It can return one of three types:

- An Unicode string ({any}`str`), a bytes string ({any}`bytes`), or a {any}`bytearray` that is passed as the first (and only) positional argument to the underlying logger.
- A tuple of `(args, kwargs)` that are passed as `log_method(*args, **kwargs)`.
- A dictionary which is passed as `log_method(**kwargs)`.

Therefore `return "hello world"` is a shortcut for `return (("hello world",), {})` (the example in {ref}`chains` assumes this shortcut has been taken).

This should give you enough power to use *structlog* with any logging system while writing agnostic processors that operate on dictionaries.

:::{versionchanged} 14.0.0 Allow final processor to return a {any}`dict`.
:::

:::{versionchanged} 20.2.0 Allow final processor to return a {any}`bytes`.
:::

:::{versionchanged} 21.2.0 Allow final processor to return a {any}`bytearray`.
:::

### Examples

The probably most useful formatter for string based loggers is {class}`structlog.processors.JSONRenderer`.
Advanced log aggregation and analysis tools like [*Logstash*](https://www.elastic.co/logstash) offer features like telling them "this is JSON, deal with it" instead of fiddling with regular expressions.

For a list of shipped processors, check out the {ref}`API documentation <procs>`.


## Redacting Sensitive Data

When logging in production environments, it's critical to ensure sensitive information like passwords, API keys, personal data, and financial information doesn't end up in your logs.
*structlog* provides the {class}`~structlog.processors.SensitiveDataRedactor` processor to automatically identify and redact sensitive fields from log events.

### Basic Usage

```python
import structlog
from structlog.processors import SensitiveDataRedactor

# Create a redactor for common sensitive fields
redactor = SensitiveDataRedactor(
    sensitive_fields=["password", "api_key", "secret", "token"]
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        redactor,  # Place before renderers!
        structlog.processors.JSONRenderer(),
    ]
)

log = structlog.get_logger()
log.info("user_login", user="alice", password="secret123")
# Output: {"event": "user_login", "user": "alice", "password": "[REDACTED]", "level": "info"}
```

### Pattern Matching

Instead of listing every possible field name, use glob-style patterns with `*` (matches any sequence) and `?` (matches single character):

```python
redactor = SensitiveDataRedactor(
    sensitive_fields=[
        "*password*",    # Matches: password, user_password, password_hash
        "api_*",         # Matches: api_key, api_secret, api_token
        "*_token",       # Matches: auth_token, refresh_token, access_token
        "*secret*",      # Matches: secret, client_secret, secret_key
    ]
)
```

### Case-Insensitive Matching

Enable case-insensitive matching when field names may have inconsistent casing:

```python
redactor = SensitiveDataRedactor(
    sensitive_fields=["password", "apikey"],
    case_insensitive=True
)
# Now matches: password, PASSWORD, Password, ApiKey, APIKEY, etc.
```

### Nested Structures

The redactor automatically traverses nested dictionaries and lists:

```python
log.info(
    "config_loaded",
    config={
        "database": {
            "host": "localhost",
            "password": "db_secret"  # Will be redacted
        },
        "api_keys": [
            {"service": "stripe", "api_key": "sk_live_xxx"},  # Will be redacted
            {"service": "twilio", "api_key": "AC_xxx"}        # Will be redacted
        ]
    }
)
```

### Custom Redaction Logic

For more control over how values are redacted, provide a custom callback:

```python
def partial_mask(field_name, value, path):
    """Show first/last 2 characters for debugging."""
    if isinstance(value, str) and len(value) > 4:
        return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
    return "[REDACTED]"

redactor = SensitiveDataRedactor(
    sensitive_fields=["*password*", "*token*"],
    redaction_callback=partial_mask
)

log.info("auth", password="mysecretpassword")
# Output: {"event": "auth", "password": "my**********rd"}
```

The callback receives:
- `field_name`: The name of the field being redacted
- `value`: The original value
- `path`: The full path to the field (e.g., `"config.database.password"`)

### Compliance Use Cases

#### GDPR Compliance

Protect personally identifiable information (PII) in logs:

```python
import logging

# Separate audit logger for compliance records
audit_logger = logging.getLogger("gdpr.audit")

def gdpr_audit(field_name, value, path):
    """Log redaction events for GDPR compliance auditing."""
    audit_logger.info(
        "PII field redacted",
        extra={
            "field_name": field_name,
            "field_path": path,
            "value_type": type(value).__name__,
        }
    )

gdpr_redactor = SensitiveDataRedactor(
    sensitive_fields=[
        # Personal identifiers
        "*email*", "*phone*", "*mobile*",
        "*name*", "*first_name*", "*last_name*",
        # Government IDs
        "*ssn*", "*social_security*", "*passport*",
        "*national_id*", "*tax_id*",
        # Location data
        "*address*", "*zip*", "*postal*",
        # Dates that could identify
        "*birth*", "*dob*",
    ],
    case_insensitive=True,
    audit_callback=gdpr_audit,
)
```

#### PCI-DSS Compliance

Protect payment card data:

```python
def mask_card_number(field_name, value, path):
    """PCI-DSS compliant card masking - show only last 4 digits."""
    if "card" in field_name.lower() and isinstance(value, str):
        # Remove any spaces/dashes and show last 4
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) >= 4:
            return f"****-****-****-{digits[-4:]}"
    return "[REDACTED]"

pci_redactor = SensitiveDataRedactor(
    sensitive_fields=[
        "*card*", "*pan*",           # Card numbers
        "*cvv*", "*cvc*", "*cvn*",   # Security codes
        "*expir*",                    # Expiration dates
        "*account_number*",           # Bank accounts
        "*routing*",                  # Routing numbers
    ],
    case_insensitive=True,
    redaction_callback=mask_card_number,
)
```

#### HIPAA Compliance

Protect health information:

```python
hipaa_redactor = SensitiveDataRedactor(
    sensitive_fields=[
        # Patient identifiers
        "*patient_id*", "*medical_record*", "*mrn*",
        # Health information
        "*diagnosis*", "*prescription*", "*medication*",
        "*treatment*", "*procedure*",
        # Insurance
        "*insurance_id*", "*policy_number*",
        # Also include general PII patterns
        "*ssn*", "*dob*", "*birth*",
    ],
    case_insensitive=True,
)
```

### Combining Multiple Redactors

For applications with different compliance requirements, you can chain multiple redactors:

```python
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        gdpr_redactor,   # GDPR PII protection
        pci_redactor,    # PCI-DSS payment data
        hipaa_redactor,  # HIPAA health data
        structlog.processors.JSONRenderer(),
    ]
)
```

### Performance Considerations

- **Prefer exact matches over patterns** when possible for better performance
- **Use `frozenset` internally** for O(1) exact match lookups
- **Patterns are compiled once** at initialization, not on every log call
- **Place the redactor before expensive operations** like JSON serialization

:::{versionadded} 25.1.0
:::


## Third-Party packages

*structlog* was specifically designed to be as composable and reusable as possible, so whatever you're missing:
chances are, you can solve it with a processor!
Since processors are self-contained callables, it's easy to write your own and to share them in separate packages.

We collect those packages in our [GitHub Wiki](https://github.com/hynek/structlog/wiki/Third-Party-Extensions) and encourage you to add your package too!
