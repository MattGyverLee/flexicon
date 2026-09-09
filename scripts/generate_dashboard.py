#!/usr/bin/env python3
"""
Generate a beautiful, interactive, self-contained HTML test dashboard
from tests/test_results.json.

Reads the test outcomes (statuses, durations, markers, tracebacks, stdout)
and writes an outstanding developer-centric HTML report at reports/dashboard.html.

Run from the repo root:

    python scripts/generate_dashboard.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Embedded HTML Template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flexicon - Test Execution Dashboard</title>
    <style>
        :root {
            --bg-primary: #0b0f19;
            --bg-secondary: #131b2e;
            --bg-card: rgba(30, 41, 59, 0.4);
            --bg-card-hover: rgba(30, 41, 59, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.15);
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --color-pass: #10b981;
            --color-pass-glow: rgba(16, 185, 129, 0.15);
            --color-fail: #ef4444;
            --color-fail-glow: rgba(239, 68, 68, 0.15);
            --color-skip: #f59e0b;
            --color-skip-glow: rgba(245, 158, 11, 0.15);
            --color-error: #ec4899;
            --color-error-glow: rgba(236, 72, 153, 0.15);
            
            --color-mock: #3b82f6;
            --color-live: #8b5cf6;
            
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            --font-mono: "Fira Code", SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-family);
            line-height: 1.5;
            padding: 2rem 1.5rem;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        /* --- HEADER & GLOWS --- */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2.5rem;
            position: relative;
        }

        header::before {
            content: '';
            position: absolute;
            top: -100px;
            left: 20%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 70%);
            z-index: -1;
            filter: blur(40px);
            pointer-events: none;
        }

        .logo-section h1 {
            font-size: 2.25rem;
            font-weight: 800;
            background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.025em;
            margin-bottom: 0.25rem;
        }

        .logo-section p {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        .timestamp {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* --- STATS GRID --- */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }

        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: transparent;
        }

        .stat-card.pass-card::before { background: var(--color-pass); }
        .stat-card.fail-card::before { background: var(--color-fail); }
        .stat-card.duration-card::before { background: #6366f1; }
        .stat-card.split-card::before { background: var(--color-mock); }

        .stat-card:hover {
            transform: translateY(-2px);
            border-color: var(--border-hover);
            box-shadow: 0 10px 20px -10px rgba(0, 0, 0, 0.5);
        }

        .stat-title {
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.75rem;
        }

        .stat-value {
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            line-height: 1;
            margin-bottom: 0.5rem;
        }

        .stat-meta {
            font-size: 0.85rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Stats Details inside card */
        .stat-details-row {
            display: flex;
            gap: 1rem;
            margin-top: 0.5rem;
        }

        .stat-detail-item {
            display: flex;
            flex-direction: column;
        }

        .stat-detail-label {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .stat-detail-val {
            font-weight: 600;
            font-size: 0.95rem;
        }

        .stat-detail-val.pass { color: var(--color-pass); }
        .stat-detail-val.fail { color: var(--color-fail); }
        .stat-detail-val.skip { color: var(--color-skip); }
        .stat-detail-val.error { color: var(--color-error); }

        /* Progress Split Bar */
        .split-bar {
            height: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 9999px;
            margin-top: 0.75rem;
            overflow: hidden;
            display: flex;
        }
        .split-bar-mock {
            height: 100%;
            background: var(--color-mock);
        }
        .split-bar-live {
            height: 100%;
            background: var(--color-live);
        }

        /* --- CONTROL BAR --- */
        .control-bar {
            background: rgba(19, 27, 46, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1rem 1.25rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }

        .search-container {
            position: relative;
            flex: 1;
            max-width: 450px;
            min-width: 260px;
        }

        .search-input {
            width: 100%;
            background: rgba(11, 15, 25, 0.7);
            border: 1px solid var(--border-color);
            padding: 0.65rem 1rem 0.65rem 2.5rem;
            border-radius: 0.75rem;
            color: var(--text-primary);
            font-size: 0.9rem;
            transition: all 0.2s;
        }

        .search-input:focus {
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
        }

        .search-icon {
            position: absolute;
            left: 0.9rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            pointer-events: none;
            width: 16px;
            height: 16px;
        }

        .filter-buttons {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .filter-btn {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 0.5rem 1rem;
            border-radius: 0.75rem;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .filter-btn:hover {
            background: rgba(30, 41, 59, 0.7);
            color: var(--text-primary);
            border-color: var(--border-hover);
        }

        .filter-btn.active {
            background: #6366f1;
            color: white;
            border-color: #6366f1;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
        }

        .filter-badge {
            background: rgba(0, 0, 0, 0.2);
            padding: 0.1rem 0.4rem;
            border-radius: 6px;
            font-size: 0.75rem;
        }

        .filter-btn.active .filter-badge {
            background: rgba(255, 255, 255, 0.2);
        }

        /* --- TREE VIEW (DOMAINS -> CLASSES -> TESTS) --- */
        .domain-list {
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .domain-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .domain-header {
            background: rgba(30, 41, 59, 0.2);
            padding: 1.25rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
            border-bottom: 1px solid transparent;
            transition: all 0.2s;
        }

        .domain-header:hover {
            background: rgba(30, 41, 59, 0.4);
        }

        .domain-card.expanded .domain-header {
            border-bottom-color: var(--border-color);
        }

        .domain-info-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .chevron {
            width: 20px;
            height: 20px;
            color: var(--text-muted);
            transition: transform 0.2s;
        }

        .domain-card.expanded .chevron {
            transform: rotate(90deg);
        }

        .domain-title-group {
            display: flex;
            flex-direction: column;
        }

        .domain-name {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .domain-summary-text {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.1rem;
        }

        .domain-info-right {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .domain-stats {
            display: flex;
            gap: 1rem;
            font-size: 0.85rem;
        }

        .domain-stat-pill {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.03);
            font-weight: 500;
        }

        .domain-stat-pill.pass { color: var(--color-pass); background: var(--color-pass-glow); }
        .domain-stat-pill.fail { color: var(--color-fail); background: var(--color-fail-glow); }
        .domain-stat-pill.skip { color: var(--color-skip); background: var(--color-skip-glow); }
        .domain-stat-pill.error { color: var(--color-error); background: var(--color-error-glow); }

        .domain-progress-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .domain-progress-bar {
            width: 100px;
            height: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 9999px;
            overflow: hidden;
        }

        .domain-progress-fill {
            height: 100%;
            background: var(--color-pass);
            border-radius: 9999px;
            transition: width 0.4s ease;
        }

        .domain-percentage {
            font-size: 0.9rem;
            font-weight: 700;
            width: 45px;
            text-align: right;
        }

        .domain-body {
            display: none;
            padding: 1.5rem;
            background: rgba(11, 15, 25, 0.3);
            flex-direction: column;
            gap: 1.25rem;
        }

        .domain-card.expanded .domain-body {
            display: flex;
        }

        /* --- CLASSES INSIDE DOMAINS --- */
        .class-group {
            background: rgba(30, 41, 59, 0.15);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            overflow: hidden;
        }

        .class-header {
            padding: 0.85rem 1.25rem;
            background: rgba(30, 41, 59, 0.25);
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
            border-bottom: 1px solid transparent;
            transition: all 0.2s;
        }

        .class-header:hover {
            background: rgba(30, 41, 59, 0.45);
        }

        .class-group.expanded .class-header {
            border-bottom-color: var(--border-color);
        }

        .class-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #c7d2fe;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .class-card.expanded .class-chevron {
            transform: rotate(90deg);
        }

        .class-stats {
            font-size: 0.8rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .class-body {
            display: none;
            padding: 0.5rem 0;
            background: rgba(11, 15, 25, 0.1);
        }

        .class-group.expanded .class-body {
            display: block;
        }

        /* --- TEST ITEM ROWS --- */
        .test-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1.25rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            cursor: pointer;
            transition: all 0.15s;
        }

        .test-row:last-child {
            border-bottom: none;
        }

        .test-row:hover {
            background: rgba(255, 255, 255, 0.02);
        }

        .test-left {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex: 1;
            min-width: 0;
        }

        .test-status-badge {
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            width: 58px;
            text-align: center;
            flex-shrink: 0;
        }

        .test-status-badge.pass { color: #059669; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); }
        .test-status-badge.fail { color: #dc2626; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); }
        .test-status-badge.skip { color: #d97706; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); }
        .test-status-badge.error { color: #db2777; background: rgba(236, 72, 153, 0.1); border: 1px solid rgba(236, 72, 153, 0.2); }

        .test-title-desc {
            display: flex;
            flex-direction: column;
            min-width: 0;
        }

        .test-name {
            font-size: 0.9rem;
            font-family: var(--font-mono);
            font-weight: 500;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .test-description {
            font-size: 0.78rem;
            color: var(--text-secondary);
            margin-top: 0.15rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .test-right {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-shrink: 0;
        }

        .type-badge {
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            letter-spacing: 0.02em;
        }

        .type-badge.mock {
            color: #60a5fa;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.15);
        }

        .type-badge.live {
            color: #a78bfa;
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.15);
        }

        .stale-badge {
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
        }

        .test-row.stale .test-name,
        .test-row.stale .test-description {
            opacity: 0.6;
        }

        .test-duration {
            font-size: 0.8rem;
            color: var(--text-muted);
            width: 60px;
            text-align: right;
            font-family: var(--font-mono);
        }

        .arrow-icon {
            width: 14px;
            height: 14px;
            color: var(--text-muted);
            opacity: 0;
            transition: all 0.15s;
        }

        .test-row:hover .arrow-icon {
            opacity: 1;
            transform: translateX(2px);
        }

        /* --- DETAILED DRAWER (RIGHT SIDEBAR) --- */
        .drawer-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(3, 7, 18, 0.6);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            z-index: 999;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }

        .drawer-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .drawer {
            position: fixed;
            top: 0;
            right: -650px;
            bottom: 0;
            width: 100%;
            max-width: 650px;
            background: #111827;
            border-left: 1px solid var(--border-color);
            z-index: 1000;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            transition: right 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .drawer.active {
            right: 0;
        }

        .drawer-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            background: rgba(30, 41, 59, 0.2);
        }

        .drawer-header-left {
            flex: 1;
            min-width: 0;
        }

        .drawer-close {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 6px;
            transition: all 0.15s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .drawer-close:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }

        .drawer-test-name {
            font-size: 1.1rem;
            font-family: var(--font-mono);
            font-weight: 700;
            color: var(--text-primary);
            word-break: break-all;
            margin-bottom: 0.5rem;
        }

        .drawer-meta-badges {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }

        .drawer-body {
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .drawer-section-title {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }

        .drawer-docstring {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            white-space: pre-wrap;
            font-style: italic;
        }

        .traceback-container {
            background: #090d16;
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            overflow: hidden;
        }

        .traceback-header {
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .traceback-header span {
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 600;
        }

        .copy-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }

        .copy-btn:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }

        .traceback-pre {
            padding: 1rem;
            overflow-x: auto;
            color: #fda4af;
            font-family: var(--font-mono);
            font-size: 0.8rem;
            line-height: 1.4;
            white-space: pre;
        }

        .output-pre {
            background: #090d16;
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1rem;
            overflow-x: auto;
            color: #cbd5e1;
            font-family: var(--font-mono);
            font-size: 0.8rem;
            line-height: 1.4;
            max-height: 250px;
        }

        /* --- EMPTY STATE --- */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            color: var(--text-secondary);
        }

        .empty-state h3 {
            font-size: 1.25rem;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        /* --- RESPONSIVE ADJUSTMENTS --- */
        @media (max-width: 768px) {
            body { padding: 1rem; }
            header { flex-direction: column; align-items: flex-start; gap: 1rem; }
            .timestamp { align-self: flex-start; }
            .control-bar { flex-direction: column; align-items: stretch; }
            .search-container { max-width: 100%; }
            .domain-info-right { display: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <header>
            <div class="logo-section">
                <h1>Flexicon</h1>
                <p>Comprehensive Test Dashboard</p>
            </div>
            <div class="timestamp" id="run-time">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span id="timestamp-val">2026-05-27 16:12:00</span>
            </div>
        </header>

        <!-- STATS GRID -->
        <div class="stats-grid">
            <!-- PASS RATE -->
            <div class="stat-card pass-card" id="card-pass-rate">
                <div class="stat-title">Pass Rate</div>
                <div class="stat-value" id="val-pass-rate">100%</div>
                <div class="stat-meta" id="val-pass-ratio">0 of 0 passed</div>
            </div>

            <!-- TOTAL TESTS -->
            <div class="stat-card" id="card-volume">
                <div class="stat-title">Test Volume</div>
                <div class="stat-value" id="val-total-tests">0</div>
                <div class="stat-details-row">
                    <div class="stat-detail-item">
                        <span class="stat-detail-label">Pass</span>
                        <span class="stat-detail-val pass" id="val-passed">0</span>
                    </div>
                    <div class="stat-detail-item">
                        <span class="stat-detail-label">Fail</span>
                        <span class="stat-detail-val fail" id="val-failed">0</span>
                    </div>
                    <div class="stat-detail-item">
                        <span class="stat-detail-label">Skip</span>
                        <span class="stat-detail-val skip" id="val-skipped">0</span>
                    </div>
                    <div class="stat-detail-item">
                        <span class="stat-detail-label">Error</span>
                        <span class="stat-detail-val error" id="val-errors">0</span>
                    </div>
                </div>
            </div>

            <!-- MOCK VS LIVE -->
            <div class="stat-card split-card">
                <div class="stat-title">Test Environment Split</div>
                <div class="stat-value" id="val-split-desc">0 / 0</div>
                <div class="stat-meta">
                    <span style="color:var(--color-mock); font-weight:600">Mock</span> vs 
                    <span style="color:var(--color-live); font-weight:600">Live (Windows)</span>
                </div>
                <div class="split-bar">
                    <div class="split-bar-mock" id="bar-mock" style="width: 50%"></div>
                    <div class="split-bar-live" id="bar-live" style="width: 50%"></div>
                </div>
            </div>

            <!-- DURATION -->
            <div class="stat-card duration-card">
                <div class="stat-title">Total Duration</div>
                <div class="stat-value" id="val-duration">0.00s</div>
                <div class="stat-meta" id="val-avg-duration">Avg: 0.00s / test</div>
            </div>
        </div>

        <!-- CONTROL BAR -->
        <div class="control-bar">
            <!-- Search -->
            <div class="search-container">
                <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input type="text" class="search-input" id="search-box" placeholder="Search tests, classes, or domains...">
            </div>
            
            <!-- Filters -->
            <div class="filter-buttons">
                <button class="filter-btn active" data-filter="all">All <span class="filter-badge" id="badge-all">0</span></button>
                <button class="filter-btn" data-filter="fail">Failures <span class="filter-badge" id="badge-fail">0</span></button>
                <button class="filter-btn" data-filter="skip">Skips <span class="filter-badge" id="badge-skip">0</span></button>
                <button class="filter-btn" data-filter="mock">Mock <span class="filter-badge" id="badge-mock">0</span></button>
                <button class="filter-btn" data-filter="live">Live <span class="filter-badge" id="badge-live">0</span></button>
            </div>
        </div>

        <!-- DOMAIN ACCORDIONS CONTAINER -->
        <div class="domain-list" id="domain-accordions">
            <!-- Dynamic Content Injected Here -->
        </div>

        <!-- EMPTY STATE -->
        <div class="empty-state" id="no-results" style="display: none;">
            <h3>No matching tests found</h3>
            <p>Try refining your search keyword or changing status filters.</p>
        </div>
    </div>

    <!-- DETAIL DRAWER -->
    <div class="drawer-overlay" id="drawer-overlay"></div>
    <div class="drawer" id="detail-drawer">
        <div class="drawer-header">
            <div class="drawer-header-left">
                <h3 class="drawer-test-name" id="drawer-test-name">test_name_goes_here</h3>
                <div class="drawer-meta-badges">
                    <span class="test-status-badge" id="drawer-status-badge">PASS</span>
                    <span class="type-badge" id="drawer-type-badge">MOCK</span>
                    <span class="timestamp" id="drawer-duration">0.05s</span>
                </div>
            </div>
            <button class="drawer-close" id="drawer-close" title="Close (Esc)">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        </div>
        <div class="drawer-body">
            <!-- Docstring -->
            <div id="section-docstring">
                <div class="drawer-section-title">Test Description</div>
                <div class="drawer-docstring" id="drawer-docstring-val"></div>
            </div>
            
            <!-- Traceback (Errors) -->
            <div id="section-traceback" style="display: none;">
                <div class="drawer-section-title">Exception Traceback</div>
                <div class="traceback-container">
                    <div class="traceback-header">
                        <span>Python Traceback</span>
                        <button class="copy-btn" id="copy-traceback">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>
                            Copy
                        </button>
                    </div>
                    <pre class="traceback-pre" id="drawer-traceback-val"></pre>
                </div>
            </div>

            <!-- Stdout -->
            <div id="section-stdout" style="display: none;">
                <div class="drawer-section-title">Captured stdout</div>
                <pre class="output-pre" id="drawer-stdout-val"></pre>
            </div>

            <!-- Stderr -->
            <div id="section-stderr" style="display: none;">
                <div class="drawer-section-title">Captured stderr</div>
                <pre class="output-pre" id="drawer-stderr-val"></pre>
            </div>
        </div>
    </div>

    <!-- DATA INJECTION PLACEHOLDER -->
    <script>
        const rawPayload = {DATA_PAYLOAD};
    </script>

    <!-- INTERACTIVE DASHBOARD SCRIPT -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const data = rawPayload;
            if (!data || !data.tests) {
                document.getElementById('domain-accordions').innerHTML = '<div class="empty-state"><h3>No execution data</h3><p>Ensure you run tests before rendering the dashboard.</p></div>';
                return;
            }

            // --- INITIALIZE STATS ---
            const sum = data.summary;
            document.getElementById('timestamp-val').textContent = new Date(data.run_timestamp).toLocaleString();
            document.getElementById('val-pass-rate').textContent = sum.pass_rate_percent + '%';
            
            // Adjust card color based on pass rate
            const passRateCard = document.getElementById('card-pass-rate');
            if (sum.pass_rate_percent === 100) {
                passRateCard.style.boxShadow = '0 0 20px -5px rgba(16, 185, 129, 0.2)';
            } else if (sum.pass_rate_percent < 90) {
                passRateCard.style.setProperty('--color-pass', 'var(--color-fail)');
                passRateCard.style.boxShadow = '0 0 20px -5px rgba(239, 68, 68, 0.2)';
            } else {
                passRateCard.style.setProperty('--color-pass', 'var(--color-skip)');
                passRateCard.style.boxShadow = '0 0 20px -5px rgba(245, 158, 11, 0.2)';
            }

            document.getElementById('val-pass-ratio').textContent = `${sum.passed} of ${sum.total} passed`;
            document.getElementById('val-total-tests').textContent = sum.total;
            document.getElementById('val-passed').textContent = sum.passed;
            document.getElementById('val-failed').textContent = sum.failed;
            document.getElementById('val-skipped').textContent = sum.skipped;
            document.getElementById('val-errors').textContent = sum.error;
            document.getElementById('val-duration').textContent = sum.duration_seconds + 's';
            
            const avg = sum.total > 0 ? (sum.duration_seconds / sum.total) : 0;
            document.getElementById('val-avg-duration').textContent = `Avg: ${avg.toFixed(3)}s / test`;

            // Environment split calculations
            const mockCount = data.tests.filter(t => t.type === 'mock').length;
            const liveCount = data.tests.filter(t => t.type === 'live').length;
            document.getElementById('val-split-desc').textContent = `${mockCount} / ${liveCount}`;
            
            const mockPercent = sum.total > 0 ? (mockCount / sum.total * 100) : 50;
            const livePercent = sum.total > 0 ? (liveCount / sum.total * 100) : 50;
            document.getElementById('bar-mock').style.width = mockPercent + '%';
            document.getElementById('bar-live').style.width = livePercent + '%';

            // Filter button badges
            document.getElementById('badge-all').textContent = sum.total;
            document.getElementById('badge-fail').textContent = sum.failed + sum.error;
            document.getElementById('badge-skip').textContent = sum.skipped;
            document.getElementById('badge-mock').textContent = mockCount;
            document.getElementById('badge-live').textContent = liveCount;

            // --- STATE VARIABLES ---
            let currentFilter = 'all';
            let searchQuery = '';
            let expandedDomains = new Set();
            let expandedClasses = new Set();

            // Expand first domain automatically on load
            const domainsList = [...new Set(data.tests.map(t => t.domain))].sort();
            if (domainsList.length > 0) {
                expandedDomains.add(domainsList[0]);
            }

            // --- RENDER ENGINE ---
            function renderDashboard() {
                const searchBox = document.getElementById('search-box');
                searchQuery = searchBox.value.toLowerCase().strip ? searchBox.value.toLowerCase().trim() : searchBox.value.toLowerCase();
                
                // Group tests
                const grouped = {};
                let matchedTestsCount = 0;

                data.tests.forEach(test => {
                    // Check search query
                    const matchesSearch = 
                        test.name.toLowerCase().includes(searchQuery) ||
                        (test.docstring && test.docstring.toLowerCase().includes(searchQuery)) ||
                        (test.class_name && test.class_name.toLowerCase().includes(searchQuery)) ||
                        test.domain.toLowerCase().includes(searchQuery);

                    // Check status filters
                    let matchesFilter = true;
                    if (currentFilter === 'fail') {
                        matchesFilter = test.status === 'fail' || test.status === 'error';
                    } else if (currentFilter === 'skip') {
                        matchesFilter = test.status === 'skip';
                    } else if (currentFilter === 'mock') {
                        matchesFilter = test.type === 'mock';
                    } else if (currentFilter === 'live') {
                        matchesFilter = test.type === 'live';
                    }

                    if (matchesSearch && matchesFilter) {
                        matchedTestsCount++;
                        
                        if (!grouped[test.domain]) {
                            grouped[test.domain] = {};
                        }
                        
                        const className = test.class_name || 'Untyped';
                        if (!grouped[test.domain][className]) {
                            grouped[test.domain][className] = [];
                        }
                        
                        grouped[test.domain][className].push(test);
                    }
                });

                const container = document.getElementById('domain-accordions');
                const noResults = document.getElementById('no-results');

                if (matchedTestsCount === 0) {
                    container.innerHTML = '';
                    noResults.style.display = 'block';
                    return;
                }
                noResults.style.display = 'none';

                let html = '';
                const sortedDomains = Object.keys(grouped).sort();

                sortedDomains.forEach(domainName => {
                    const classes = grouped[domainName];
                    const isDomainExpanded = expandedDomains.has(domainName) || searchQuery !== '';
                    
                    // Aggregate stats for this domain based on matching tests
                    let domTotal = 0;
                    let domPass = 0;
                    let domFail = 0;
                    let domSkip = 0;
                    let domError = 0;

                    Object.values(classes).forEach(tList => {
                        tList.forEach(t => {
                            domTotal++;
                            if (t.status === 'pass') domPass++;
                            else if (t.status === 'fail') domFail++;
                            else if (t.status === 'skip') domSkip++;
                            else if (t.status === 'error') domError++;
                        });
                    });

                    const domPassRate = domTotal > 0 ? Math.round(domPass / domTotal * 100) : 0;
                    const domSummary = `${domTotal} tests: ${domPass} passed, ${domFail + domError} failed`;

                    html += `
                    <div class="domain-card ${isDomainExpanded ? 'expanded' : ''}" data-domain="${domainName}">
                        <div class="domain-header">
                            <div class="domain-info-left">
                                <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                <div class="domain-title-group">
                                    <span class="domain-name">${domainName}</span>
                                    <span class="domain-summary-text">${domSummary}</span>
                                </div>
                            </div>
                            <div class="domain-info-right">
                                <div class="domain-stats">
                                    <span class="domain-stat-pill pass">${domPass}</span>
                                    ${domFail + domError > 0 ? `<span class="domain-stat-pill fail">${domFail + domError}</span>` : ''}
                                    ${domSkip > 0 ? `<span class="domain-stat-pill skip">${domSkip}</span>` : ''}
                                </div>
                                <div class="domain-progress-container">
                                    <div class="domain-progress-bar">
                                        <div class="domain-progress-fill" style="width: ${domPassRate}%; ${domPassRate < 90 ? (domPassRate < 50 ? 'background-color: var(--color-fail)' : 'background-color: var(--color-skip)') : ''}"></div>
                                    </div>
                                    <span class="domain-percentage">${domPassRate}%</span>
                                </div>
                            </div>
                        </div>
                        <div class="domain-body">
                    `;

                    // Render Operations Classes
                    const sortedClasses = Object.keys(classes).sort();
                    sortedClasses.forEach(clsName => {
                        const tests = classes[clsName];
                        const classKey = `${domainName}::${clsName}`;
                        const isClassExpanded = expandedClasses.has(classKey) || searchQuery !== '';
                        
                        let clsPassCount = tests.filter(t => t.status === 'pass').length;
                        let clsFailCount = tests.filter(t => t.status === 'fail' || t.status === 'error').length;
                        
                        html += `
                            <div class="class-group ${isClassExpanded ? 'expanded' : ''}" data-class-key="${classKey}">
                                <div class="class-header">
                                    <span class="class-title">
                                        <svg class="chevron class-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                        ${clsName}
                                    </span>
                                    <span class="class-stats">
                                        ${clsPassCount} / ${tests.length} passed
                                        ${clsFailCount > 0 ? `<span class="domain-stat-pill fail" style="padding:0.05rem 0.35rem; font-size:0.75rem">${clsFailCount}</span>` : ''}
                                    </span>
                                </div>
                                <div class="class-body">
                        `;

                        // Render Test Rows
                        tests.forEach(test => {
                            const isStale = test.last_run_timestamp && data.run_timestamp && test.last_run_timestamp !== data.run_timestamp;
                            html += `
                                <div class="test-row ${isStale ? 'stale' : ''}" data-nodeid="${test.nodeid}">
                                    <div class="test-left">
                                        <span class="test-status-badge ${test.status}">${test.status}</span>
                                        <div class="test-title-desc">
                                            <span class="test-name">${test.name}</span>
                                            ${test.docstring ? `<span class="test-description">${test.docstring}</span>` : ''}
                                        </div>
                                    </div>
                                    <div class="test-right">
                                        ${isStale ? `<span class="stale-badge" title="Not in latest run; last seen ${test.last_run_timestamp}">stale</span>` : ''}
                                        <span class="type-badge ${test.type}">${test.type}</span>
                                        <span class="test-duration">${test.duration.toFixed(3)}s</span>
                                        <svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                                    </div>
                                </div>
                            `;
                        });

                        html += `
                                </div>
                            </div>
                        `;
                    });

                    html += `
                        </div>
                    </div>
                    `;
                });

                container.innerHTML = html;

                // Bind Accordion Listeners
                document.querySelectorAll('.domain-header').forEach(header => {
                    header.addEventListener('click', (e) => {
                        const card = header.closest('.domain-card');
                        const domName = card.getAttribute('data-domain');
                        if (expandedDomains.has(domName)) {
                            expandedDomains.delete(domName);
                            card.classList.remove('expanded');
                        } else {
                            expandedDomains.add(domName);
                            card.classList.add('expanded');
                        }
                    });
                });

                document.querySelectorAll('.class-header').forEach(header => {
                    header.addEventListener('click', (e) => {
                        const group = header.closest('.class-group');
                        const key = group.getAttribute('data-class-key');
                        if (expandedClasses.has(key)) {
                            expandedClasses.delete(key);
                            group.classList.remove('expanded');
                        } else {
                            expandedClasses.add(key);
                            group.classList.add('expanded');
                        }
                    });
                });

                // Bind Test Row Clicking
                document.querySelectorAll('.test-row').forEach(row => {
                    row.addEventListener('click', () => {
                        const nodeid = row.getAttribute('data-nodeid');
                        const testObj = data.tests.find(t => t.nodeid === nodeid);
                        if (testObj) {
                            openDrawer(testObj);
                        }
                    });
                });
            }

            // --- DETAILED DRAWER LOGIC ---
            const drawer = document.getElementById('detail-drawer');
            const overlay = document.getElementById('drawer-overlay');
            const closeBtn = document.getElementById('drawer-close');
            let currentOpenTraceback = '';

            function openDrawer(test) {
                document.getElementById('drawer-test-name').textContent = test.name;
                
                const statusBadge = document.getElementById('drawer-status-badge');
                statusBadge.className = `test-status-badge ${test.status}`;
                statusBadge.textContent = test.status;

                const typeBadge = document.getElementById('drawer-type-badge');
                typeBadge.className = `type-badge ${test.type}`;
                typeBadge.textContent = test.type;

                document.getElementById('drawer-duration').textContent = test.duration.toFixed(3) + 's';

                // Description
                const docVal = document.getElementById('drawer-docstring-val');
                if (test.docstring) {
                    docVal.textContent = test.docstring;
                    document.getElementById('section-docstring').style.display = 'block';
                } else {
                    document.getElementById('section-docstring').style.display = 'none';
                }

                // Traceback
                const tbSec = document.getElementById('section-traceback');
                if (test.traceback) {
                    document.getElementById('drawer-traceback-val').textContent = test.traceback;
                    currentOpenTraceback = test.traceback;
                    tbSec.style.display = 'block';
                } else {
                    tbSec.style.display = 'none';
                    currentOpenTraceback = '';
                }

                // Captured Output (Stdout/Stderr)
                const stdoutSec = document.getElementById('section-stdout');
                if (test.stdout && test.stdout.trim()) {
                    document.getElementById('drawer-stdout-val').textContent = test.stdout;
                    stdoutSec.style.display = 'block';
                } else {
                    stdoutSec.style.display = 'none';
                }

                const stderrSec = document.getElementById('section-stderr');
                if (test.stderr && test.stderr.trim()) {
                    document.getElementById('drawer-stderr-val').textContent = test.stderr;
                    stderrSec.style.display = 'block';
                } else {
                    stderrSec.style.display = 'none';
                }

                drawer.classList.add('active');
                overlay.classList.add('active');
            }

            function closeDrawer() {
                drawer.classList.remove('active');
                overlay.classList.remove('active');
            }

            closeBtn.addEventListener('click', closeDrawer);
            overlay.addEventListener('click', closeDrawer);

            // Close on escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    closeDrawer();
                }
            });

            // Copy Traceback
            document.getElementById('copy-traceback').addEventListener('click', () => {
                if (currentOpenTraceback) {
                    navigator.clipboard.writeText(currentOpenTraceback).then(() => {
                        const copyBtnText = document.querySelector('#copy-traceback');
                        const originalHtml = copyBtnText.innerHTML;
                        copyBtnText.textContent = 'Copied!';
                        setTimeout(() => {
                            copyBtnText.innerHTML = originalHtml;
                        }, 1500);
                    });
                }
            });

            // --- FILTER CONTROLS BINDING ---
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentFilter = btn.getAttribute('data-filter');
                    renderDashboard();
                });
            });

            // Search input binding (debounced slightly or on input)
            let searchTimeout = null;
            document.getElementById('search-box').addEventListener('input', () => {
                if (searchTimeout) clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    renderDashboard();
                }, 100);
            });

            // First run
            renderDashboard();
        });
    </script>
</body>
</html>
"""


def _recompute_summary(tests: list) -> dict:
    """Recompute the summary block from a list of test result dicts."""
    total = len(tests)
    passed = sum(1 for t in tests if t.get("status") == "pass")
    failed = sum(1 for t in tests if t.get("status") == "fail")
    skipped = sum(1 for t in tests if t.get("status") == "skip")
    error = sum(1 for t in tests if t.get("status") == "error")
    duration = round(sum(float(t.get("duration") or 0) for t in tests), 3)
    pass_rate = round(passed / total * 100, 1) if total else 0
    return {
        "duration_seconds": duration,
        "error": error,
        "failed": failed,
        "pass_rate_percent": pass_rate,
        "passed": passed,
        "skipped": skipped,
        "total": total,
    }


def _merge_with_persistent(latest_payload: dict, persistent_path: Path) -> dict:
    """
    Merge the latest run's test results into a persistent store keyed by nodeid.

    Tests present in `latest_payload` overwrite the persistent entry. Tests
    not in the latest run keep their previous status (and their previous
    `last_run_timestamp`), so they don't disappear from the dashboard.

    Writes the merged payload back to `persistent_path` and returns it.
    """
    latest_ts = latest_payload.get("run_timestamp")
    latest_tests = latest_payload.get("tests", []) or []

    by_nodeid: dict = {}
    if persistent_path.exists():
        try:
            existing = json.loads(persistent_path.read_text(encoding="utf-8-sig"))
            for t in existing.get("tests", []) or []:
                nid = t.get("nodeid")
                if nid:
                    by_nodeid[nid] = t
        except Exception as exc:
            print(
                f"[WARN] Could not read persistent store {persistent_path}: {exc}. "
                "Starting fresh.",
                file=sys.stderr,
            )
            by_nodeid = {}

    for t in latest_tests:
        nid = t.get("nodeid")
        if not nid:
            continue
        merged = dict(t)
        merged["last_run_timestamp"] = latest_ts
        by_nodeid[nid] = merged

    merged_tests = sorted(by_nodeid.values(), key=lambda x: x.get("nodeid", ""))

    merged_payload = {
        "run_timestamp": latest_ts,
        "summary": _recompute_summary(merged_tests),
        "tests": merged_tests,
    }

    try:
        persistent_path.parent.mkdir(parents=True, exist_ok=True)
        persistent_path.write_text(
            json.dumps(merged_payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
            newline="\n",
        )
    except Exception as exc:
        print(f"[WARN] Could not write persistent store {persistent_path}: {exc}", file=sys.stderr)

    return merged_payload


def generate_dashboard_from_json(
    json_path_str: str | None = None,
    *,
    persist: bool = True,
    reset: bool = False,
    persistent_path_str: str | None = None,
) -> int:
    """Read structured test results JSON and render the interactive dashboard HTML."""
    here = Path(__file__).resolve().parent
    repo_root = here.parent

    # Resolve paths
    default_json = repo_root / "tests" / "test_results.json"
    json_path = Path(json_path_str).resolve() if json_path_str else default_json
    out_path = repo_root / "reports" / "dashboard.html"
    persistent_path = (
        Path(persistent_path_str).resolve()
        if persistent_path_str
        else repo_root / "tests" / "test_results_persistent.json"
    )

    if reset and persistent_path.exists():
        try:
            persistent_path.unlink()
            print(f"[OK] Reset persistent store at {persistent_path}")
        except Exception as exc:
            print(f"[WARN] Could not delete {persistent_path}: {exc}", file=sys.stderr)

    if not json_path.exists():
        print(f"[WARN] Test results JSON does not exist at {json_path}. Run the tests first.", file=sys.stderr)
        return 1

    try:
        payload_text = json_path.read_text(encoding="utf-8-sig")
        payload_data = json.loads(payload_text)
    except Exception as exc:
        print(f"[ERROR] Failed to read or parse {json_path}: {exc}", file=sys.stderr)
        return 1

    if persist:
        latest_count = len(payload_data.get("tests", []) or [])
        payload_data = _merge_with_persistent(payload_data, persistent_path)
        merged_count = len(payload_data.get("tests", []) or [])
        stale_count = merged_count - latest_count
        print(
            f"[OK] Merged {latest_count} test(s) from this run into {merged_count} persisted test(s) "
            f"({stale_count} retained from previous runs) -> {persistent_path}"
        )

    # Inject JSON payload into the HTML template
    html_content = HTML_TEMPLATE.replace("{DATA_PAYLOAD}", json.dumps(payload_data, ensure_ascii=False))

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_content, encoding="utf-8", newline="\n")
        print(f"[OK] Wrote interactive dashboard to {out_path}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Failed to write {out_path}: {exc}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "json_path",
        nargs="?",
        default=None,
        help="Path to test_results.json (defaults to tests/test_results.json)",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Render directly from this run's JSON without merging into the persistent store",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe the persistent store before merging (start fresh)",
    )
    parser.add_argument(
        "--persistent-path",
        default=None,
        help="Override the persistent store path (default: tests/test_results_persistent.json)",
    )
    args = parser.parse_args(argv)
    return generate_dashboard_from_json(
        args.json_path,
        persist=not args.no_persist,
        reset=args.reset,
        persistent_path_str=args.persistent_path,
    )


if __name__ == "__main__":
    sys.exit(main())
