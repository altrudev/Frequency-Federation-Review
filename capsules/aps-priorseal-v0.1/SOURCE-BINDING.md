# APS owner-source binding

The APS commit pin is not treated as established merely because the repository was cloned.

For the proposed APS × PriorSeal run, the adapter receives two distinct local roots:

1. the owner APS fixture root at commit `948f99b85343bef2c6fa677c8543965caacfc087`;
2. the copied APS fixture root embedded in PriorSeal at commit `d749d2691c3e6be139de4020e7b27cdafca2c428`.

The verifier requires the manifest at each root to hash to:

`2bf365bc9124ecfc943d5be86c34e8e0cacd51a5929b8d0c906e633a017231f9`

It then requires the two manifest files to be byte-for-byte identical and compares all 17 manifest-declared files byte-for-byte.

Only after that comparison succeeds does the adapter emit:

`composition.aps_owner_fixture_copy.byte_identical = ESTABLISHED`

Any manifest mismatch, missing file, changed owner byte, or changed copied byte causes a fail-closed process error before report publication.

Files present only in the PriorSeal copy and not declared by the APS owner manifest are not used to establish this source-binding claim.
