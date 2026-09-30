# Ubuntu "server" with systemd + SSH, so Ansible can manage it like a real VM.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends systemd systemd-sysv openssh-server sudo python3 ca-certificates \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Deployment user with passwordless sudo
RUN useradd --create-home --shell /bin/bash ansible \
 && echo "ansible ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ansible \
 && chmod 0440 /etc/sudoers.d/ansible

# Key-only SSH. The public key is mounted from ./keys at runtime.
RUN printf '%s\n' \
      'PasswordAuthentication no' \
      'PermitRootLogin no' \
      'StrictModes no' \
      'AuthorizedKeysFile /etc/ssh/lab_keys/id_ed25519.pub' \
      > /etc/ssh/sshd_config.d/lab.conf \
 && systemctl enable ssh

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
