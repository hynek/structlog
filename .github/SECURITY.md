# Security Policy

## Supported Versions

We are following [*CalVer*](https://calver.org) with generous backwards-compatibility guarantees.
Therefore we only support the latest version.

That said, you shouldn't be afraid to upgrade *structlog* if you're using its documented public APIs and pay attention to `DeprecationWarning`s.
Whenever there is a need to break compatibility, it is announced [in the changelog](https://github.com/hynek/structlog/blob/main/CHANGELOG.md) and raises a `DeprecationWarning` for a year (if possible) before it's finally really broken.

You **can't** rely on the default settings and the `structlog.dev` module, though.
They may be adjusted in the future to provide a better experience when starting to use *structlog*.
So please make sure to **always** properly configure your applications.


## Reporting a Vulnerability

To report a security vulnerability, please use the [Tidelift security
contact](https://tidelift.com/security). Tidelift will coordinate the fix and
disclosure.
