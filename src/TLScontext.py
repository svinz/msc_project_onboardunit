class TLScontext:

    @staticmethod
    def create_tls_context(ca_certs=None, certfile=None, keyfile=None, cert_reqs=None, tls_version=None, ciphers=None):
        """Configure network encryption and authentication options. Enables SSL/TLS support.
        ca_certs : a string path to the Certificate Authority certificate files
        that are to be treated as trusted by this client. If this is the only
        option given then the client will operate in a similar manner to a web
        browser. That is to say it will require the broker to have a
        certificate signed by the Certificate Authorities in ca_certs and will
        communicate using TLS v1, but will not attempt any form of
        authentication. This provides basic network encryption but may not be
        sufficient depending on how the broker is configured.
        By default, on Python 2.7.9+ or 3.4+, the default certification
        authority of the system is used. On older Python version this parameter
        is mandatory.
        certfile and keyfile are strings pointing to the PEM encoded client
        certificate and private keys respectively. If these arguments are not
        None then they will be used as client information for TLS based
        authentication.  Support for this feature is broker dependent. Note
        that if either of these files in encrypted and needs a password to
        decrypt it, Python will ask for the password at the command line. It is
        not currently possible to define a callback to provide the password.
        cert_reqs allows the certificate requirements that the client imposes
        on the broker to be changed. By default this is ssl.CERT_REQUIRED,
        which means that the broker must provide a certificate. See the ssl
        pydoc for more information on this parameter.
        tls_version allows the version of the SSL/TLS protocol used to be
        specified. By default TLS v1 is used. Previous versions (all versions
        beginning with SSL) are possible but not recommended due to possible
        security problems.
        ciphers is a string specifying which encryption ciphers are allowable
        for this connection, or None to use the defaults. See the ssl pydoc for
        more information.
        Must be called before connect() or connect_async()."""

        ssl = None
        try:
            import ssl
        except ImportError:
            pass

        if ssl is None:
            raise ValueError('This platform has no SSL/TLS.')

        if not hasattr(ssl, 'SSLContext'):
            # Require Python version that has SSL context support in standard library
            raise ValueError(
                'Python 2.7.9 and 3.2 are the minimum supported versions for TLS.')

        if ca_certs is None and not hasattr(ssl.SSLContext, 'load_default_certs'):
            raise ValueError('ca_certs must not be None.')

        # Create SSLContext object
        if tls_version is None:
            tls_version = ssl.PROTOCOL_TLSv1
            # If the python version supports it, use highest TLS version automatically
            if hasattr(ssl, "PROTOCOL_TLS"):
                tls_version = ssl.PROTOCOL_TLS
        context = ssl.SSLContext(tls_version)

        # Configure context
        if certfile is not None:
            context.load_cert_chain(certfile, keyfile)

        if cert_reqs == ssl.CERT_NONE and hasattr(context, 'check_hostname'):
            context.check_hostname = False

        context.verify_mode = ssl.CERT_REQUIRED if cert_reqs is None else cert_reqs

        if ca_certs is not None:
            context.load_verify_locations(ca_certs)
        else:
            context.load_default_certs()

        if ciphers is not None:
            context.set_ciphers(ciphers)
        return context
        # self.tls_set_context(context)

        # if cert_reqs != ssl.CERT_NONE:
        #     # Default to secure, sets context.check_hostname attribute
        #     # if available
        #     self.tls_insecure_set(False)
        # else:
        #     # But with ssl.CERT_NONE, we can not check_hostname
        #     self.tls_insecure_set(True)
