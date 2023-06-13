# Security Policy

## Supported Versions

We are following [*CalVer*](https://calver.org) with generous backwards-compatibility guarantees.
Therefore we only support the latest version.

Put simply, you shouldn't ever be afraid to upgrade as long as you're only using our public APIs.
Whenever there is a need to break compatibility, it is announced in the changelog, and raises a `DeprecationWarning` for a year (if possible) before it's finally really broken.

You **can't** rely on the default settings and the `structlog.dev` module, though.
They may be adjusted in the future to provide a better experience when starting to use *structlog*.
So please make sure to **always** properly configure your applications.


## Reporting a Vulnerability

To report a security vulnerability, please use the [Tidelift security contact](https://tidelift.com/security).
Tidelift will coordinate the fix and disclosure.
