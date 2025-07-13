#!/bin/bash
# Quick approval script

if [ "$1" = "y" ] || [ "$1" = "yes" ]; then
    echo "y" > approval_response.txt
    echo "✅ Approved"
elif [ "$1" = "n" ] || [ "$1" = "no" ]; then
    echo "n" > approval_response.txt
    echo "❌ Denied"
elif [ "$1" = "a" ] || [ "$1" = "all" ]; then
    echo "a" > approval_response.txt
    echo "✅ Approved all"
else
    echo "Usage: ./approve.sh [y|n|a]"
    echo "  y - Approve this request"
    echo "  n - Deny this request"
    echo "  a - Approve all future requests of this type"
fi