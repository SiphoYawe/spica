"use client";

import React, { Component, type ReactNode } from "react";
import {
	Card,
	CardContent,
	CardHeader,
	CardTitle,
	CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorBoundaryProps {
	children: ReactNode;
}

interface ErrorBoundaryState {
	hasError: boolean;
	error: Error | null;
	errorInfo: React.ErrorInfo | null;
}

export default class ErrorBoundary extends Component<
	ErrorBoundaryProps,
	ErrorBoundaryState
> {
	constructor(props: ErrorBoundaryProps) {
		super(props);
		this.state = {
			hasError: false,
			error: null,
			errorInfo: null,
		};
	}

	static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
		return { hasError: true, error };
	}

	componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
		console.error("ErrorBoundary caught an error:", error, errorInfo);
		this.setState({
			error,
			errorInfo,
		});
	}

	handleReset = () => {
		this.setState({
			hasError: false,
			error: null,
			errorInfo: null,
		});
		window.location.reload();
	};

	render() {
		if (this.state.hasError) {
			return (
				<div className="min-h-screen flex items-center justify-center p-8 bg-darker-bg">
					<Card className="max-w-2xl w-full border-cyber-red/30 bg-gradient-to-br from-card to-darker-bg shadow-[0_0_24px_rgba(255,65,108,0.15)]">
						<div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-cyber-red to-cyber-purple opacity-60" />

						<CardHeader className="text-center space-y-4">
							<div className="flex justify-center">
								<div className="rounded-full bg-cyber-red/10 p-4">
									<AlertCircle className="h-12 w-12 text-cyber-red" />
								</div>
							</div>
							<CardTitle className="font-display text-3xl">
								Something Went Wrong
							</CardTitle>
							<CardDescription className="text-base">
								The application encountered an unexpected error.
							</CardDescription>
						</CardHeader>

						<CardContent className="space-y-6">
							{/* Error Details */}
							{this.state.error && (
								<div className="rounded-lg border border-card-border bg-darker-bg/50 p-4 space-y-2">
									<p className="text-sm font-semibold text-muted-foreground">
										Error Details:
									</p>
									<p className="font-mono text-sm text-cyber-red break-words">
										{this.state.error.message}
									</p>

									{process.env.NODE_ENV === "development" &&
										this.state.errorInfo && (
											<details className="mt-4">
												<summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
													Stack trace (development only)
												</summary>
												<pre className="mt-2 text-xs text-muted-foreground overflow-auto max-h-48 p-2 bg-darker-bg rounded">
													{this.state.errorInfo.componentStack}
												</pre>
											</details>
										)}
								</div>
							)}

							{/* Action Buttons */}
							<div className="flex flex-col sm:flex-row gap-3">
								<Button
									onClick={this.handleReset}
									variant="cyber"
									size="lg"
									className="flex-1 gap-2">
									<RefreshCw className="h-4 w-4" />
									Reload Application
								</Button>
								<Button
									onClick={() => window.history.back()}
									variant="outline"
									size="lg"
									className="flex-1">
									Go Back
								</Button>
							</div>

							{/* Help Text */}
							<div className="text-center text-sm text-muted-foreground">
								<p>
									If this problem persists, please contact support or check the
									browser console for more details.
								</p>
							</div>
						</CardContent>
					</Card>
				</div>
			);
		}

		return this.props.children;
	}
}
