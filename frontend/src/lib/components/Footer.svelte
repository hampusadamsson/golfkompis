<footer class="border-t bg-muted/40 py-10 text-sm text-muted-foreground">
	<div class="mx-auto flex max-w-5xl flex-col items-center gap-4 px-4 text-center sm:flex-row sm:justify-between sm:text-left">
		<p class="font-medium text-foreground">Golfkompis</p>

		<nav class="flex flex-wrap justify-center gap-x-6 gap-y-2 sm:justify-end" aria-label="Sidfotslänkar">
			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
			<a href="/terms" class="hover:text-foreground transition-colors">Användarvillkor</a>
		</nav>

		<p class="text-xs">
			Golfkompis är inte anslutet till SGF eller Min Golf. &copy; {new Date().getFullYear()}
		</p>
	</div>
</footer>
